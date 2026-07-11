# -*- coding: utf-8 -*-
"""
AI 推理服务 — 独立进程 :8001
仅加载 PyTorch 模型，不涉及业务逻辑
"""
import logging
import io
import os
from contextlib import asynccontextmanager
from pathlib import Path

import torch
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from PIL import Image

from backend.config import AI_SERVICE_PORT, LLM_MODEL_PATH, LLM_USE_LOCAL
from backend.shared.constants import CLASS_NAMES, CLASS_NAME_CN, CLASS_NAME_RAG_KEY, IMG_SIZE, IMG_MEAN, IMG_STD

logger = logging.getLogger(__name__)

# ─── Global model handles ───
model = None
llm = None
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')


def load_llm():
    """加载本地 GGUF 模型（llama-cpp）"""
    global llm
    model_path = Path(LLM_MODEL_PATH)
    if not model_path.exists() or not LLM_USE_LOCAL:
        logger.info(f'llama-cpp 模型未找到或不启用: {model_path}')
        return None
    try:
        from llama_cpp import Llama
        llm = Llama(
            model_path=str(model_path),
            n_ctx=4096,
            n_threads=4,
            n_gpu_layers=-1 if torch.cuda.is_available() else 0,
            verbose=False,
        )
        logger.info(f'llama-cpp 模型已加载: {model_path.name}')
    except Exception as e:
        logger.warning(f'llama-cpp 加载失败: {e}，使用模拟模式')
    return llm


def load_model():
    """加载 LSNet 模型"""
    global model
    project_root = Path(__file__).resolve().parent.parent
    override_dir = project_root / 'lsnet' / 'checkpoints'
    model_paths = sorted(override_dir.glob('*.pth'))
    
    if not model_paths:
        models_dir = project_root / 'lsnet' / 'models'
        model_paths = sorted(models_dir.rglob('best_model.pth'))
    
    if not model_paths:
        logger.warning('未找到 .pth 模型文件，使用模拟模式')
        return None
    model_path = model_paths[-1]

    from lsnet.arch import build_model
    model = build_model(num_classes=len(CLASS_NAMES))
    state = torch.load(model_path, map_location=device)
    if 'model_state_dict' in state:
        model.load_state_dict(state['model_state_dict'])
    else:
        model.load_state_dict(state)
    model.to(device)
    model.eval()
    logger.info(f'模型已加载: {model_path.name} ({device})')
    return model


def preprocess_image(image_bytes: bytes) -> torch.Tensor:
    """图像预处理 → 模型输入 tensor"""
    img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
    from torchvision import transforms
    transform = transforms.Compose([
        transforms.Resize((IMG_SIZE, IMG_SIZE)),
        transforms.ToTensor(),
        transforms.Normalize(mean=IMG_MEAN, std=IMG_STD),
    ])
    return transform(img).unsqueeze(0).to(device)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info('=' * 60)
    logger.info('AI 推理服务启动中...')
    logger.info(f'设备: {device}')
    logger.info('=' * 60)
    load_model()
    load_llm()
    yield
    logger.info('AI 推理服务关闭')


app = FastAPI(title='AI 推理服务', version='2.0.0', lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_credentials=True,
                   allow_methods=['*'], allow_headers=['*'])


@app.post('/ai/predict')
async def predict(file: UploadFile = File(...)):
    """图像病害识别"""
    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail='图片大小不能超过 10MB')

    content_type = file.content_type
    if not content_type or not content_type.startswith('image/'):
        ext = file.filename.split('.')[-1].lower() if file.filename else ''
        ext_map = {'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'png': 'image/png', 'webp': 'image/webp', 'gif': 'image/gif'}
        if ext in ext_map:
            content_type = ext_map[ext]
        else:
            raise HTTPException(status_code=400, detail='仅支持图片文件')

    if model is None:
        import random
        idx = random.randint(0, len(CLASS_NAMES) - 1)
        class_name = CLASS_NAMES[idx]
        return {
            'disease_name': CLASS_NAME_CN.get(class_name, class_name),
            'confidence': round(random.uniform(0.65, 0.98), 4),
            'risk_level': random.choice(['无', '低', '中等', '高']),
            'class_name': class_name,
            'rag_key': CLASS_NAME_RAG_KEY.get(class_name, ''),
        }

    tensor = preprocess_image(contents)
    with torch.no_grad():
        outputs = model(tensor)
        probs = torch.softmax(outputs, dim=1)
        confidence, pred_idx = torch.max(probs, dim=1)

    class_name = CLASS_NAMES[pred_idx.item()]
    return {
        'disease_name': CLASS_NAME_CN.get(class_name, class_name),
        'confidence': round(confidence.item(), 4),
        'risk_level': '中等',
        'class_name': class_name,
        'rag_key': CLASS_NAME_RAG_KEY.get(class_name, ''),
    }


@app.get('/ai/health')
def health():
    return {'status': 'ok', 'service': 'ai', 'device': str(device), 'model_loaded': model is not None}


# ─── Pydantic model for chat ───
class ChatRequest(BaseModel):
    query: str
    context: str = ''


@app.post('/ai/chat')
async def chat(req: ChatRequest):
    """AI对话 — 优先使用本地 llama-cpp GGUF 模型，回退到 Qwen API / Mock"""
    system_prompt = (
        '你是一个专业的农业病虫害诊断助手。'
        '根据用户描述的病害症状、作物信息和已有知识，给出专业的诊断和治疗建议。'
        '回答简洁专业，使用中文。'
    )

    # 1. 优先使用本地 llama-cpp 模型
    if llm is not None:
        try:
            from asyncio import to_thread
            prompt = f"<|system|>\n{system_prompt}</s>\n<|user|>\n{req.query}</s>\n<|assistant|>\n"
            result = await to_thread(
                llm.create_chat_completion,
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': req.query},
                ],
                temperature=0.7,
                max_tokens=2048,
            )
            reply = result['choices'][0]['message']['content']
            return {'response': reply, 'model': 'qwen2-1.5b-gguf-local'}
        except Exception as e:
            logger.warning(f'llama-cpp 推理失败，回退: {e}')

    # 2. 回退：Qwen API
    qwen_key = os.environ.get('QWEN_API_KEY', '')
    if qwen_key:
        try:
            import httpx
            messages = [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': req.query},
            ]
            if req.context:
                messages.insert(1, {'role': 'assistant', 'content': req.context})

            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(
                    os.environ.get('QWEN_API_URL', 'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions'),
                    headers={'Authorization': f'Bearer {qwen_key}', 'Content-Type': 'application/json'},
                    json={
                        'model': os.environ.get('QWEN_MODEL', 'qwen-plus'),
                        'messages': messages,
                        'temperature': 0.7,
                        'max_tokens': 2048,
                    },
                )
                resp.raise_for_status()
                reply = resp.json()['choices'][0]['message']['content']
                return {'response': reply, 'model': 'qwen-plus'}
        except Exception as e:
            return {'response': f'Qwen API error: {str(e)}', 'model': 'mock'}

    # 3. 最终回退：Mock
    mock_reply = (
        f'关于"{req.query}"的诊断建议：\n\n'
        f'1. 根据您描述的症状，可能是真菌性病害（如白粉病、锈病、灰霉病等）或细菌性病害。\n'
        f'2. 推荐方案：初期可选用保护性杀菌剂（如代森锰锌）全园喷施预防。\n'
        f'3. 环境管理：加强通风透光，降低田间湿度，及时清除病残体。\n'
        f'4. 注意：以上为模拟诊断参考，请结合实际症状判断。如需精准诊断，请上传图片或联系当地植保部门。'
    )
    return {'response': mock_reply, 'model': 'mock'}


if __name__ == '__main__':
    import uvicorn
    uvicorn.run('ai_service.main:app', host='0.0.0.0', port=AI_SERVICE_PORT)
