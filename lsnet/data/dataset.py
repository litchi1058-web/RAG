# -*- coding: utf-8 -*-
"""
LSNet 数据集类
支持多种数据集格式
"""
import os
import random
from pathlib import Path
from PIL import Image
import torch
from torch.utils.data import Dataset
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.shared.paths import get_raw_data_dir, get_plantvillage_dir


class FruitDiseaseDataset(Dataset):
    """果蔬病害数据集"""

    def __init__(self, samples, transform=None):
        """
        Args:
            samples: list of (image_path, label) tuples
            transform: 数据增强 transform
        """
        self.samples = samples
        self.transform = transform

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        img_path, label = self.samples[idx]
        try:
            image = Image.open(img_path).convert('RGB')
        except Exception as e:
            print(f"图片加载失败: {img_path}, 错误: {e}")
            image = Image.new('RGB', (224, 224))

        if self.transform:
            image = self.transform(image)

        return image, label


class CustomDataset(Dataset):
    """
    自定义数据集类（原 data1）
    目录结构：
    - 训练集/1/, 训练集/2/, ..., 训练集/9/
    - 测试集/1/, 测试集/2/, ..., 测试集/9/
    """
    
    def __init__(self, root_dir, split='train', transform=None):
        """
        Args:
            root_dir: str 数据集根目录（custom/）
            split: str 'train' 或 'test'
            transform: 数据增强 transform
        """
        self.root_dir = Path(root_dir)
        self.split = split
        self.transform = transform
        self.samples = []
        self.class_to_idx = {}
        
        self._load_samples()
    
    def _load_samples(self):
        """加载数据集样本"""
        split_dir = self.root_dir / ('训练集' if self.split == 'train' else '测试集')
        
        if not split_dir.exists():
            raise ValueError(f"数据集目录不存在: {split_dir}")
        
        # 获取所有类别目录（按数字排序）
        class_dirs = sorted([d for d in split_dir.iterdir() if d.is_dir()], 
                           key=lambda x: int(x.name))
        
        self.class_to_idx = {str(i + 1): i for i in range(len(class_dirs))}
        
        for class_dir in class_dirs:
            class_name = class_dir.name
            label = self.class_to_idx[class_name]
            
            for img_path in class_dir.glob("*.*"):
                if img_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.bmp']:
                    self.samples.append((str(img_path), label))
        
        print(f"Custom {self.split} 数据集: {len(self.samples)} 样本, {len(self.class_to_idx)} 类别")
    
    def __len__(self):
        return len(self.samples)
    
    def __getitem__(self, idx):
        img_path, label = self.samples[idx]
        try:
            image = Image.open(img_path).convert('RGB')
        except Exception as e:
            print(f"图片加载失败: {img_path}, 错误: {e}")
            image = Image.new('RGB', (224, 224))
        
        if self.transform:
            image = self.transform(image)
        
        return image, label


def collect_all_samples(root_dir):
    """
    收集指定目录下所有样本
    Returns:
        samples: list of (image_path, label)
        class_to_idx: dict
    """
    samples = []
    class_to_idx = {}

    root_path = Path(root_dir)
    if root_path.exists():
        classes = sorted([d.name for d in root_path.iterdir() if d.is_dir()])
        class_to_idx = {cls_name: i for i, cls_name in enumerate(classes)}

        for class_name in classes:
            class_dir = root_path / class_name
            for img_path in class_dir.glob("*.*"):
                if img_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.bmp']:
                    samples.append((str(img_path), class_to_idx[class_name]))

    return samples, class_to_idx


def load_custom_dataset(root_dir, split='train'):
    """
    加载自定义数据集（原 data1）
    
    Args:
        root_dir: str 数据集根目录（custom/）
        split: str 'train' 或 'test'
        
    Returns:
        dataset: CustomDataset
        class_to_idx: dict
    """
    dataset = CustomDataset(root_dir, split=split, transform=None)
    return dataset, dataset.class_to_idx


def load_custom_samples(root_dir, split='train'):
    """
    加载自定义数据集样本列表（原 data1）
    
    Args:
        root_dir: str 数据集根目录（custom/）
        split: str 'train' 或 'test'
        
    Returns:
        samples: list of (image_path, label)
        class_to_idx: dict
    """
    dataset = CustomDataset(root_dir, split=split, transform=None)
    return dataset.samples, dataset.class_to_idx


def load_plantvillage_data(plantvillage_dir=None):
    """加载 PlantVillage 数据集"""
    from backend.shared.constants import PLANTVILLAGE_CLASSES

    if plantvillage_dir is None:
        plantvillage_dir = get_plantvillage_dir()

    samples = []
    class_to_idx = {cls_name: i for i, cls_name in enumerate(PLANTVILLAGE_CLASSES)}

    plantvillage_path = Path(plantvillage_dir)
    if plantvillage_path.exists():
        for class_name in PLANTVILLAGE_CLASSES:
            class_dir = plantvillage_path / class_name
            if class_dir.exists():
                for img_path in class_dir.glob("*.jpg"):
                    samples.append((str(img_path), class_to_idx[class_name]))

    print(f"PlantVillage 数据集: {len(samples)} 样本")
    return samples, class_to_idx


def split_dataset(samples, train_ratio=0.7, val_ratio=0.1, test_ratio=0.2, seed=42):
    """按比例划分数据集"""
    random.seed(seed)
    shuffled = samples.copy()
    random.shuffle(shuffled)

    total = len(shuffled)
    train_end = int(total * train_ratio)
    val_end = train_end + int(total * val_ratio)

    train_samples = shuffled[:train_end]
    val_samples = shuffled[train_end:val_end]
    test_samples = shuffled[val_end:]

    print(f"数据集划分: 训练集 {len(train_samples)} ({train_ratio*100:.0f}%), "
          f"验证集 {len(val_samples)} ({val_ratio*100:.0f}%), "
          f"测试集 {len(test_samples)} ({test_ratio*100:.0f}%)")

    return train_samples, val_samples, test_samples


def split_dataset_stratified(samples, train_ratio=0.7, val_ratio=0.1, test_ratio=0.2, seed=42):
    """
    分层划分数据集（保持类别分布）
    
    Args:
        samples: list of (image_path, label)
        train_ratio: float 训练集比例
        val_ratio: float 验证集比例
        test_ratio: float 测试集比例
        seed: int 随机种子
        
    Returns:
        train_samples, val_samples, test_samples: list of (image_path, label)
    """
    random.seed(seed)
    
    # 按类别分组
    class_samples = {}
    for img_path, label in samples:
        if label not in class_samples:
            class_samples[label] = []
        class_samples[label].append((img_path, label))
    
    train_samples = []
    val_samples = []
    test_samples = []
    
    for label, label_samples in class_samples.items():
        random.shuffle(label_samples)
        total = len(label_samples)
        train_end = int(total * train_ratio)
        val_end = train_end + int(total * val_ratio)
        
        train_samples.extend(label_samples[:train_end])
        val_samples.extend(label_samples[train_end:val_end])
        test_samples.extend(label_samples[val_end:])
    
    # 打乱顺序
    random.shuffle(train_samples)
    random.shuffle(val_samples)
    random.shuffle(test_samples)
    
    print(f"分层划分 - 训练集 {len(train_samples)}, 验证集 {len(val_samples)}, 测试集 {len(test_samples)}")
    
    return train_samples, val_samples, test_samples


def merge_datasets(samples_list):
    """
    合并多个数据集样本
    
    Args:
        samples_list: list of list of (image_path, label)
        
    Returns:
        merged_samples: list of (image_path, label)
    """
    merged = []
    for samples in samples_list:
        merged.extend(samples)
    return merged


def get_class_distribution(samples):
    """
    获取类别分布
    
    Args:
        samples: list of (image_path, label)
        
    Returns:
        dict: {label: count}
    """
    distribution = {}
    for _, label in samples:
        distribution[label] = distribution.get(label, 0) + 1
    return distribution


def calculate_class_weights(samples, num_classes):
    """
    计算类别权重（用于处理类别不平衡）
    
    Args:
        samples: list of (image_path, label)
        num_classes: int 类别数量
        
    Returns:
        torch.Tensor: 类别权重
    """
    distribution = get_class_distribution(samples)
    total_samples = len(samples)
    
    weights = []
    for i in range(num_classes):
        count = distribution.get(i, 1)
        weights.append(total_samples / (num_classes * count))
    
    return torch.tensor(weights)