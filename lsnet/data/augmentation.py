# -*- coding: utf-8 -*-
"""
高级数据增强模块
实现 MixUp、CutMix、Cutout 等增强技术
"""
import random
import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image, ImageEnhance, ImageOps

try:
    import cv2
except ImportError:
    cv2 = None


def mixup_data(x, y, alpha=1.0, device='cuda'):
    """
    MixUp 数据增强
    
    Args:
        x: torch.Tensor 输入图像张量 (batch_size, channels, height, width)
        y: torch.Tensor 标签 (batch_size,)
        alpha: float Beta 分布参数
        device: str 设备类型
        
    Returns:
        mixed_x: torch.Tensor 混合后的图像
        y_a: torch.Tensor 原始标签
        y_b: torch.Tensor 混合标签
        lam: float 混合比例
    """
    if alpha > 0:
        lam = np.random.beta(alpha, alpha)
    else:
        lam = 1.0
    
    batch_size = x.size()[0]
    index = torch.randperm(batch_size).to(device)
    
    mixed_x = lam * x + (1 - lam) * x[index, :]
    y_a, y_b = y, y[index]
    
    return mixed_x, y_a, y_b, lam


def mixup_criterion(criterion, pred, y_a, y_b, lam):
    """
    MixUp 损失函数
    
    Args:
        criterion: 损失函数
        pred: torch.Tensor 模型预测
        y_a: torch.Tensor 原始标签
        y_b: torch.Tensor 混合标签
        lam: float 混合比例
        
    Returns:
        loss: torch.Tensor 损失值
    """
    return lam * criterion(pred, y_a) + (1 - lam) * criterion(pred, y_b)


def cutmix_data(x, y, alpha=1.0, device='cuda'):
    """
    CutMix 数据增强
    
    Args:
        x: torch.Tensor 输入图像张量 (batch_size, channels, height, width)
        y: torch.Tensor 标签 (batch_size,)
        alpha: float Beta 分布参数
        device: str 设备类型
        
    Returns:
        mixed_x: torch.Tensor 混合后的图像
        y_a: torch.Tensor 原始标签
        y_b: torch.Tensor 混合标签
        lam: float 混合比例
    """
    if alpha > 0:
        lam = np.random.beta(alpha, alpha)
    else:
        lam = 1.0
    
    batch_size = x.size()[0]
    index = torch.randperm(batch_size).to(device)
    
    _, _, h, w = x.size()
    
    # 随机裁剪区域
    cut_rat = np.sqrt(1. - lam)
    cut_w = int(w * cut_rat)
    cut_h = int(h * cut_rat)
    
    # 随机位置
    cx = np.random.randint(w)
    cy = np.random.randint(h)
    
    bbx1 = np.clip(cx - cut_w // 2, 0, w)
    bby1 = np.clip(cy - cut_h // 2, 0, h)
    bbx2 = np.clip(cx + cut_w // 2, 0, w)
    bby2 = np.clip(cy + cut_h // 2, 0, h)
    
    # 执行 CutMix
    x[:, :, bby1:bby2, bbx1:bbx2] = x[index, :, bby1:bby2, bbx1:bbx2]
    
    # 调整混合比例
    lam = 1 - ((bbx2 - bbx1) * (bby2 - bby1) / (w * h))
    
    y_a, y_b = y, y[index]
    
    return x, y_a, y_b, lam


def cutout(x, hole_size=16, num_holes=1, fill_value=0):
    """
    Cutout 数据增强
    
    Args:
        x: torch.Tensor 输入图像张量 (batch_size, channels, height, width)
        hole_size: int 孔洞大小
        num_holes: int 孔洞数量
        fill_value: float 填充值
        
    Returns:
        x: torch.Tensor 处理后的图像
    """
    _, _, h, w = x.size()
    
    for n in range(num_holes):
        y = np.random.randint(h)
        x_coord = np.random.randint(w)
        
        y1 = np.clip(y - hole_size // 2, 0, h)
        y2 = np.clip(y + hole_size // 2, 0, h)
        x1 = np.clip(x_coord - hole_size // 2, 0, w)
        x2 = np.clip(x_coord + hole_size // 2, 0, w)
        
        x[:, :, y1:y2, x1:x2] = fill_value
    
    return x


def random_erase(x, p=0.5, scale=(0.02, 0.33), ratio=(0.3, 3.3), value=0):
    """
    Random Erasing 数据增强
    
    Args:
        x: torch.Tensor 输入图像张量 (batch_size, channels, height, width)
        p: float 应用概率
        scale: tuple 擦除区域面积比例范围
        ratio: tuple 擦除区域宽高比范围
        value: float 填充值
        
    Returns:
        x: torch.Tensor 处理后的图像
    """
    if random.random() > p:
        return x
    
    _, _, h, w = x.size()
    area = h * w
    
    target_area = random.uniform(*scale) * area
    aspect_ratio = random.uniform(*ratio)
    
    h_erase = int(round(np.sqrt(target_area * aspect_ratio)))
    w_erase = int(round(np.sqrt(target_area / aspect_ratio)))
    
    if w_erase < w and h_erase < h:
        x1 = random.randint(0, w - w_erase)
        y1 = random.randint(0, h - h_erase)
        
        if isinstance(value, (int, float)):
            x[:, :, y1:y1 + h_erase, x1:x1 + w_erase] = value
        else:
            x[:, :, y1:y1 + h_erase, x1:x1 + w_erase] = torch.from_numpy(np.array(value)).view(-1, 1, 1)
    
    return x


def random_rotation(image, max_degrees=15):
    """
    随机旋转图像（PIL Image）
    
    Args:
        image: PIL.Image 输入图像
        max_degrees: float 最大旋转角度
        
    Returns:
        PIL.Image: 旋转后的图像
    """
    degrees = random.uniform(-max_degrees, max_degrees)
    return image.rotate(degrees, expand=False)


def random_flip(image, flip_prob=0.5):
    """
    随机翻转图像（PIL Image）
    
    Args:
        image: PIL.Image 输入图像
        flip_prob: float 翻转概率
        
    Returns:
        PIL.Image: 翻转后的图像
    """
    if random.random() < flip_prob:
        image = image.transpose(Image.FLIP_LEFT_RIGHT)
    if random.random() < flip_prob:
        image = image.transpose(Image.FLIP_TOP_BOTTOM)
    
    return image


def random_crop(image, crop_size, padding=4):
    """
    随机裁剪（带填充）
    
    Args:
        image: PIL.Image 输入图像
        crop_size: tuple 裁剪尺寸
        padding: int 填充大小
        
    Returns:
        PIL.Image: 裁剪后的图像
    """
    # 添加填充
    image = ImageOps.expand(image, border=padding, fill=0)
    
    # 随机选择裁剪区域
    width, height = image.size
    x = random.randint(0, width - crop_size[0])
    y = random.randint(0, height - crop_size[1])
    
    return image.crop((x, y, x + crop_size[0], y + crop_size[1]))


def random_color_jitter(image, brightness=0.2, contrast=0.2, saturation=0.2, hue=0.1):
    """
    随机颜色抖动
    
    Args:
        image: PIL.Image 输入图像
        brightness: float 亮度调整范围
        contrast: float 对比度调整范围
        saturation: float 饱和度调整范围
        hue: float 色相调整范围
        
    Returns:
        PIL.Image: 颜色调整后的图像
    """
    # 随机调整亮度
    if brightness > 0:
        enhancer = ImageEnhance.Brightness(image)
        image = enhancer.enhance(random.uniform(1 - brightness, 1 + brightness))
    
    # 随机调整对比度
    if contrast > 0:
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(random.uniform(1 - contrast, 1 + contrast))
    
    # 随机调整饱和度
    if saturation > 0:
        enhancer = ImageEnhance.Color(image)
        image = enhancer.enhance(random.uniform(1 - saturation, 1 + saturation))
    
    # 随机调整色相（注意：色相调整在 PIL 中需要特殊处理）
    if hue > 0:
        image_array = np.array(image)
        hsv = cv2.cvtColor(image_array, cv2.COLOR_RGB2HSV)
        hsv[:, :, 0] = (hsv[:, :, 0] + random.uniform(-hue * 180, hue * 180)) % 180
        image = Image.fromarray(cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB))
    
    return image


def random_grayscale(image, p=0.1):
    """
    随机灰度化
    
    Args:
        image: PIL.Image 输入图像
        p: float 灰度化概率
        
    Returns:
        PIL.Image: 处理后的图像
    """
    if random.random() < p:
        image = image.convert('L').convert('RGB')
    return image


def random_resized_crop(image, size, scale=(0.08, 1.0), ratio=(3/4, 4/3)):
    """
    随机缩放裁剪
    
    Args:
        image: PIL.Image 输入图像
        size: tuple 输出尺寸
        scale: tuple 缩放比例范围
        ratio: tuple 宽高比范围
        
    Returns:
        PIL.Image: 裁剪后的图像
    """
    width, height = image.size
    
    # 随机选择面积比例
    area = width * height
    target_area = random.uniform(*scale) * area
    
    # 随机选择宽高比
    aspect_ratio = random.uniform(*ratio)
    
    # 计算裁剪尺寸
    w = int(round(np.sqrt(target_area * aspect_ratio)))
    h = int(round(np.sqrt(target_area / aspect_ratio)))
    
    # 确保尺寸不超过原图
    w = min(w, width)
    h = min(h, height)
    
    # 随机选择裁剪位置
    x = random.randint(0, width - w)
    y = random.randint(0, height - h)
    
    # 裁剪并调整大小
    crop = image.crop((x, y, x + w, y + h))
    return crop.resize(size, Image.Resampling.LANCZOS)


class AugmentationPipeline:
    """
    数据增强管道
    
    支持多种增强技术的组合使用
    """
    
    def __init__(self, mixup_alpha=0.8, cutmix_alpha=1.0, cutout_prob=0.5, 
                 cutout_hole_size=64, use_mixup=True, use_cutmix=True):
        """
        Args:
            mixup_alpha: float MixUp Beta 参数
            cutmix_alpha: float CutMix Beta 参数
            cutout_prob: float Cutout 应用概率
            cutout_hole_size: int Cutout 孔洞大小
            use_mixup: bool 是否使用 MixUp
            use_cutmix: bool 是否使用 CutMix
        """
        self.mixup_alpha = mixup_alpha
        self.cutmix_alpha = cutmix_alpha
        self.cutout_prob = cutout_prob
        self.cutout_hole_size = cutout_hole_size
        self.use_mixup = use_mixup
        self.use_cutmix = use_cutmix
    
    def apply_batch_augmentation(self, x, y, device='cuda'):
        """
        对批次数据应用增强
        
        Args:
            x: torch.Tensor 输入图像张量
            y: torch.Tensor 标签
            device: str 设备类型
            
        Returns:
            x: torch.Tensor 增强后的图像
            y_a: torch.Tensor 原始标签
            y_b: torch.Tensor 混合标签（如果使用 MixUp/CutMix）
            lam: float 混合比例（如果使用 MixUp/CutMix）
        """
        # 随机选择使用 MixUp 还是 CutMix
        if self.use_mixup and self.use_cutmix:
            if random.random() < 0.5:
                return mixup_data(x, y, self.mixup_alpha, device)
            else:
                return cutmix_data(x, y, self.cutmix_alpha, device)
        elif self.use_mixup:
            return mixup_data(x, y, self.mixup_alpha, device)
        elif self.use_cutmix:
            return cutmix_data(x, y, self.cutmix_alpha, device)
        
        return x, y, y, 1.0
    
    def apply_cutout(self, x):
        """
        应用 Cutout
        
        Args:
            x: torch.Tensor 输入图像张量
            
        Returns:
            x: torch.Tensor 处理后的图像
        """
        if random.random() < self.cutout_prob:
            return cutout(x, self.cutout_hole_size)
        return x