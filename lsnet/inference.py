# -*- coding: utf-8 -*-
"""
LSNet 模型推理
提供 Python API 供后端调用
"""
import os
import sys
from pathlib import Path
import json

import torch
import torch.nn as nn
from torchvision import transforms
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.shared.paths import (
    get_checkpoints_dir, get_results_dir
)
from backend.shared.constants import (
    IMG_SIZE, IMAGENET_MEAN, IMAGENET_STD, CLASS_NAMES
)


class LSNetInference:
    """LSNet 模型推理封装"""

    def __init__(self, model_name='lsnet', checkpoint_path=None, device=None):
        """
        Args:
            model_name: 模型名称（lsnet/mobilenetv2/efficientnetb0）
            checkpoint_path: 模型权重路径（默认使用 best_model.pth）
            device: 推理设备（默认自动）
        """
        self.model_name = model_name
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')

        # 权重路径
        if checkpoint_path is None:
            ckpt_dir = Path(get_checkpoints_dir()) / model_name
            checkpoint_path = ckpt_dir / "best_model.pth"

        self.checkpoint_path = Path(checkpoint_path)

        # 类别映射 (必须在加载模型之前设置)
        self.class_names = CLASS_NAMES

        # 加载模型
        self.model = self._load_model()
        self.model.eval()

        # 图像预处理
        self.transform = transforms.Compose([
            transforms.Resize((IMG_SIZE, IMG_SIZE)),
            transforms.ToTensor(),
            transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD)
        ])

    def _load_model(self):
        """加载模型"""
        from lsnet.arch.builder import build_model

        model = build_model(
            self.model_name,
            num_classes=len(self.class_names),
            pretrained=False
        )

        if self.checkpoint_path.exists():
            state_dict = torch.load(
                self.checkpoint_path, map_location=self.device
            )
            if isinstance(state_dict, dict) and 'state_dict' in state_dict:
                state_dict = state_dict['state_dict']
            model.load_state_dict(state_dict, strict=False)
            print(f"加载权重: {self.checkpoint_path}")
        else:
            print(f"⚠️ 权重文件不存在: {self.checkpoint_path}")
            print("将使用未训练模型进行推理")

        return model.to(self.device)

    @torch.no_grad()
    def predict(self, image_path, top_k=3):
        """
        单张图片推理
        Args:
            image_path: 图片路径
            top_k: 返回 top-k 结果
        Returns:
            dict: {disease_key, confidence, top_k: [...]}
        """
        # 加载并预处理
        image = Image.open(image_path).convert('RGB')
        image_tensor = self.transform(image).unsqueeze(0).to(self.device)

        # 推理
        outputs = self.model(image_tensor)
        probs = torch.softmax(outputs, dim=1)[0]

        # Top-K
        top_probs, top_indices = torch.topk(probs, top_k)
        results = []
        for prob, idx in zip(top_probs.cpu().tolist(), top_indices.cpu().tolist()):
            results.append({
                'class_index': idx,
                'class_name': self.class_names[idx],
                'confidence': round(prob, 4)
            })

        return {
            'disease_key': results[0]['class_name'],
            'confidence': results[0]['confidence'],
            'top_k': results
        }

    @torch.no_grad()
    def predict_batch(self, image_paths, batch_size=16):
        """批量推理"""
        results = []
        for path in image_paths:
            try:
                r = self.predict(path)
                results.append({'image': str(path), 'success': True, **r})
            except Exception as e:
                results.append({
                    'image': str(path),
                    'success': False,
                    'error': str(e)
                })
        return results


# 简易推理（无 PyTorch 时使用 mock）
class MockInference:
    """模拟推理（无模型时使用）"""

    def __init__(self, *args, **kwargs):
        self.class_names = CLASS_NAMES

    def predict(self, image_path, top_k=3):
        import random
        idx = random.randint(0, len(self.class_names) - 1)
        return {
            'disease_key': self.class_names[idx],
            'confidence': 0.85,
            'top_k': [{'class_name': self.class_names[idx], 'confidence': 0.85}],
            'mock': True
        }

    def predict_batch(self, image_paths, *args, **kwargs):
        return [self.predict(p) for p in image_paths]


def get_inference_engine(model_name='lsnet', **kwargs):
    """获取推理引擎（自动选择）"""
    try:
        return LSNetInference(model_name, **kwargs)
    except Exception as e:
        print(f"加载真实模型失败: {e}，使用 Mock 推理")
        return MockInference(**kwargs)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='LSNet 推理')
    parser.add_argument('--image', type=str, required=True, help='图片路径')
    parser.add_argument('--model', type=str, default='lsnet', help='模型名称')
    args = parser.parse_args()

    engine = get_inference_engine(args.model)
    result = engine.predict(args.image)
    print(json.dumps(result, ensure_ascii=False, indent=2))
