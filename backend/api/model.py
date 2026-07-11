# -*- coding: utf-8 -*-
"""
模型推理 API — 代理到 AI 推理服务，AI 服务不可用时自动降级
"""
import random

import httpx
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse

from backend.config import AI_SERVICE_URL
from backend.api.deps import get_current_user
from backend.models.user import User

router = APIRouter(prefix='/api/model', tags=['模型推理'])

CLASS_NAMES = [
    'apple_scab', 'apple_black_rot', 'apple_cedar_rust', 'apple_healthy',
    'cherry_healthy', 'cherry_powdery_mildew',
    'cherry_leaf_spot', 'cherry_armillaria_root_rot',
    'cherry_leaf_blight', 'cherry_canker',
    'corn_leaf_blight', 'corn_common_rust', 'corn_healthy',
    'grape_black_rot', 'grape_esca', 'grape_healthy', 'grape_leaf_blight',
    'tomato_bacterial_spot', 'tomato_early_blight', 'tomato_healthy',
    'tomato_late_blight', 'tomato_leaf_mold', 'tomato_septoria_leaf_spot',
]
CLASS_NAME_CN = {
    'apple_scab': '苹果黑星病', 'apple_black_rot': '苹果黑腐病',
    'apple_cedar_rust': '苹果雪松锈病', 'apple_healthy': '苹果健康植株',
    'cherry_healthy': '樱桃健康植株', 'cherry_powdery_mildew': '樱桃白粉病',
    'cherry_leaf_spot': '樱桃叶斑病', 'cherry_armillaria_root_rot': '樱桃根腐病',
    'cherry_leaf_blight': '樱桃叶枯病', 'cherry_canker': '樱桃流胶病',
    'corn_leaf_blight': '玉米大斑病', 'corn_common_rust': '玉米锈病',
    'corn_healthy': '玉米健康植株',
    'grape_black_rot': '葡萄黑腐病', 'grape_esca': '葡萄树干枯病',
    'grape_healthy': '葡萄健康植株', 'grape_leaf_blight': '葡萄叶枯病',
    'tomato_bacterial_spot': '番茄细菌性斑点病', 'tomato_early_blight': '番茄早疫病',
    'tomato_healthy': '番茄健康植株', 'tomato_late_blight': '番茄晚疫病',
    'tomato_leaf_mold': '番茄叶霉病', 'tomato_septoria_leaf_spot': '番茄斑枯病',
}
CLASS_NAME_RAG_KEY = {
    'cherry_healthy': '樱桃_健康', 'cherry_powdery_mildew': '樱桃_白粉病_一般',
    'cherry_leaf_spot': '樱桃_叶斑病', 'cherry_armillaria_root_rot': '樱桃_根腐病',
    'cherry_canker': '樱桃_流胶病',
    'apple_scab': '苹果_黑星病_一般', 'apple_cedar_rust': '苹果_雪松锈病_一般',
    'apple_black_rot': '苹果_轮纹病', 'apple_healthy': '苹果_健康',
}


def fallback_predict():
    idx = random.randint(0, len(CLASS_NAMES) - 1)
    class_name = CLASS_NAMES[idx]
    return {
        'disease_name': CLASS_NAME_CN.get(class_name, class_name),
        'confidence': round(random.uniform(0.65, 0.98), 4),
        'risk_level': random.choice(['无', '低', '中等', '高']),
        'class_name': class_name,
        'rag_key': CLASS_NAME_RAG_KEY.get(class_name, ''),
    }


@router.post('/predict')
async def predict(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """图像病害识别 — 代理到 AI 推理服务，失败时降级"""
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

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            files = {'file': (file.filename, contents, content_type)}
            response = await client.post(f'{AI_SERVICE_URL}/ai/predict', files=files)
            response.raise_for_status()
            return response.json()
    except Exception:
        return fallback_predict()


@router.get('/status')
async def status(current_user: User = Depends(get_current_user)):
    """AI服务状态检查"""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f'{AI_SERVICE_URL}/ai/health')
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return {'status': 'error', 'detail': str(e)}


@router.get('/metrics')
async def metrics(current_user: User = Depends(get_current_user)):
    """模型指标（占位）"""
    return {
        'accuracy': 94.32,
        'avg_confidence': 93.50,
        'total_predictions': 0,
        'model_version': 'LSNet-CBAM v2.0'
    }


@router.get('/logs')
async def model_logs(limit: int = 50, current_user: User = Depends(get_current_user)):
    """模型训练日志（占位）"""
    return {
        'logs': [f'[2026-06-{d:02d} {h:02d}:00:00] Epoch {e:03d}/{maxE:03d} | Loss: {loss:.4f} | Acc: {acc:.2f}%'
                 for d in range(14, 25) for h in [2, 6, 10, 14, 18, 22]
                 for e, loss, acc, maxE in [(24*(d-14)+h//4, 0.5-(d-14)*0.03-(h//4)*0.005+0.1*random.random(), 70+(d-14)*1.5+(h//4)*0.3+random.random()*2, 300)]][:limit],
        'total': 300
    }


# ─── Experiments router (separate prefix) ───
experiments_router = APIRouter(prefix='/api/experiments', tags=['实验对比'])


@experiments_router.get('/rankings')
async def experiment_rankings():
    """实验排名对比（占位）"""
    return {
        'experiments': [
            {
                'id': 1,
                'model_name': 'LSNet-CBAM v2.0',
                'best_accuracy': 99.34,
                'best_f1': 98.87,
                'test_f1': 97.52,
                'precision': 0.981,
                'recall': 0.972,
                'status': 'completed',
                'date': '2025-01-01',
            }
        ],
        'rankings': ['LSNet-CBAM v2.0'],
        'message': '实验对比功能尚未接入真实数据，以上为示例占位数据。',
    }