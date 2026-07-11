# -*- coding: utf-8 -*-
"""
数据增强和预处理
"""
from torchvision import transforms
import torch
import numpy as np
import random
from PIL import Image, ImageOps
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.shared import IMAGE_SIZE, IMG_MEAN, IMG_STD


def get_train_transform(image_size=None):
    """训练集数据增强"""
    if image_size is None:
        image_size = IMAGE_SIZE

    return transforms.Compose([
        transforms.Resize((image_size + 32, image_size + 32)),
        transforms.RandomCrop(image_size),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomVerticalFlip(p=0.3),
        transforms.RandomRotation(degrees=15),
        transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
        transforms.ToTensor(),
        transforms.Normalize(mean=IMG_MEAN, std=IMG_STD),
    ])


def get_val_transform(image_size=None):
    """验证/测试集数据预处理"""
    if image_size is None:
        image_size = IMAGE_SIZE

    return transforms.Compose([
        transforms.Resize((image_size, image_size)),
        transforms.ToTensor(),
        transforms.Normalize(mean=IMG_MEAN, std=IMG_STD),
    ])


def get_strong_transform(image_size=None):
    """更强的数据增强（适用于小数据集）"""
    if image_size is None:
        image_size = IMAGE_SIZE

    return transforms.Compose([
        transforms.Resize((image_size + 64, image_size + 64)),
        transforms.RandomResizedCrop(image_size, scale=(0.7, 1.0)),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomVerticalFlip(p=0.3),
        transforms.RandomRotation(degrees=30),
        transforms.RandomPerspective(distortion_scale=0.2, p=0.3),
        transforms.ColorJitter(
            brightness=0.3,
            contrast=0.3,
            saturation=0.3,
            hue=0.1
        ),
        transforms.RandomGrayscale(p=0.1),
        transforms.ToTensor(),
        transforms.Normalize(mean=IMG_MEAN, std=IMG_STD),
        transforms.RandomErasing(p=0.5, scale=(0.02, 0.2), ratio=(0.3, 3.3)),
    ])


def get_simple_transform(image_size=None):
    """简单的预处理（仅调整大小和归一化）"""
    if image_size is None:
        image_size = IMAGE_SIZE

    return transforms.Compose([
        transforms.Resize((image_size, image_size)),
        transforms.ToTensor(),
        transforms.Normalize(mean=IMG_MEAN, std=IMG_STD),
    ])


class RandomGaussianNoise:
    """随机高斯噪声"""
    
    def __init__(self, mean=0.0, std=0.05):
        self.mean = mean
        self.std = std
    
    def __call__(self, tensor):
        noise = torch.randn(tensor.size()) * self.std + self.mean
        return tensor + noise


class RandomCutout:
    """Cutout 增强"""
    
    def __init__(self, hole_size=64, p=0.5):
        self.hole_size = hole_size
        self.p = p
    
    def __call__(self, tensor):
        if random.random() < self.p:
            _, h, w = tensor.size()
            y = random.randint(0, h - self.hole_size)
            x = random.randint(0, w - self.hole_size)
            tensor[:, y:y+self.hole_size, x:x+self.hole_size] = 0
        return tensor


class CustomResize:
    """自定义调整大小，保持宽高比并填充"""
    
    def __init__(self, size, pad_color=(0.485, 0.456, 0.406)):
        self.size = size
        self.pad_color = pad_color
    
    def __call__(self, image):
        original_width, original_height = image.size
        target_width, target_height = self.size
        
        scale = min(target_width / original_width, target_height / original_height)
        new_width = int(original_width * scale)
        new_height = int(original_height * scale)
        
        image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        new_image = Image.new('RGB', self.size, tuple(int(c * 255) for c in self.pad_color))
        x_offset = (target_width - new_width) // 2
        y_offset = (target_height - new_height) // 2
        new_image.paste(image, (x_offset, y_offset))
        
        return new_image


def get_transforms(transform_type='train', image_size=None, **kwargs):
    """
    获取指定类型的变换
    
    Args:
        transform_type: str 变换类型 ('train', 'val', 'test', 'strong', 'simple')
        image_size: int 图像尺寸
        **kwargs: 额外参数
        
    Returns:
        torchvision.transforms.Compose 变换组合
    """
    if image_size is None:
        image_size = IMAGE_SIZE
    
    transform_map = {
        'train': get_train_transform,
        'val': get_val_transform,
        'test': get_val_transform,
        'strong': get_strong_transform,
        'simple': get_simple_transform,
    }
    
    if transform_type not in transform_map:
        raise ValueError(f"未知的变换类型: {transform_type}")
    
    return transform_map[transform_type](image_size)


def create_mixed_transform(image_size=None, use_strong=False, use_cutout=False):
    """
    创建混合变换
    
    Args:
        image_size: int 图像尺寸
        use_strong: bool 是否使用强增强
        use_cutout: bool 是否使用 Cutout
        
    Returns:
        torchvision.transforms.Compose 变换组合
    """
    if image_size is None:
        image_size = IMAGE_SIZE
    
    transform_list = []
    
    if use_strong:
        transform_list.extend([
            transforms.Resize((image_size + 64, image_size + 64)),
            transforms.RandomResizedCrop(image_size, scale=(0.7, 1.0)),
        ])
    else:
        transform_list.extend([
            transforms.Resize((image_size + 32, image_size + 32)),
            transforms.RandomCrop(image_size),
        ])
    
    transform_list.extend([
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomVerticalFlip(p=0.3),
        transforms.RandomRotation(degrees=15),
        transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
    ])
    
    transform_list.append(transforms.ToTensor())
    transform_list.append(transforms.Normalize(mean=IMG_MEAN, std=IMG_STD))
    
    if use_cutout:
        transform_list.append(RandomCutout(hole_size=image_size // 4))
    
    return transforms.Compose(transform_list)