# -*- coding: utf-8 -*-
"""
数据预处理模块
提供图像预处理的工具函数
"""
import os
import cv2
import numpy as np
from PIL import Image, ImageOps
from pathlib import Path


def load_image(image_path):
    """
    加载图像并转换为RGB格式
    
    Args:
        image_path: 图像文件路径
        
    Returns:
        PIL.Image: RGB格式图像
    """
    try:
        image = Image.open(image_path).convert('RGB')
        return image
    except Exception as e:
        print(f"图像加载失败: {image_path}, 错误: {e}")
        return Image.new('RGB', (224, 224))


def resize_and_pad(image, target_size, pad_color=(128, 128, 128)):
    """
    调整图像大小并保持宽高比，空白区域填充指定颜色
    
    Args:
        image: PIL.Image 输入图像
        target_size: tuple (width, height) 目标尺寸
        pad_color: tuple 填充颜色，默认灰色
        
    Returns:
        PIL.Image: 调整后的图像
    """
    original_width, original_height = image.size
    target_width, target_height = target_size
    
    # 计算缩放比例
    scale = min(target_width / original_width, target_height / original_height)
    new_width = int(original_width * scale)
    new_height = int(original_height * scale)
    
    # 缩放图像
    image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    # 创建目标图像并填充
    new_image = Image.new('RGB', target_size, pad_color)
    
    # 计算居中位置
    x_offset = (target_width - new_width) // 2
    y_offset = (target_height - new_height) // 2
    
    new_image.paste(image, (x_offset, y_offset))
    
    return new_image


def normalize_image(image, mean=None, std=None):
    """
    图像归一化处理
    
    Args:
        image: PIL.Image 输入图像
        mean: list 均值，默认 ImageNet 均值
        std: list 标准差，默认 ImageNet 标准差
        
    Returns:
        numpy.ndarray: 归一化后的图像数组
    """
    if mean is None:
        mean = [0.485, 0.456, 0.406]
    if std is None:
        std = [0.229, 0.224, 0.225]
    
    image_array = np.array(image).astype(np.float32) / 255.0
    
    # 归一化
    image_array = (image_array - mean) / std
    
    return image_array


def apply_clahe(image, clip_limit=2.0, grid_size=(8, 8)):
    """
    应用 CLAHE 直方图均衡化增强对比度
    
    Args:
        image: PIL.Image 输入图像
        clip_limit: float 对比度限制
        grid_size: tuple 网格大小
        
    Returns:
        PIL.Image: 增强后的图像
    """
    image_array = np.array(image)
    
    # 转换为 YUV 颜色空间
    yuv = cv2.cvtColor(image_array, cv2.COLOR_RGB2YUV)
    y, u, v = cv2.split(yuv)
    
    # 应用 CLAHE
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=grid_size)
    y_equalized = clahe.apply(y)
    
    # 合并通道
    yuv_equalized = cv2.merge((y_equalized, u, v))
    result = cv2.cvtColor(yuv_equalized, cv2.COLOR_YUV2RGB)
    
    return Image.fromarray(result)


def adjust_gamma(image, gamma=1.0):
    """
    调整图像伽马值
    
    Args:
        image: PIL.Image 输入图像
        gamma: float 伽马值
        
    Returns:
        PIL.Image: 调整后的图像
    """
    image_array = np.array(image).astype(np.float32) / 255.0
    image_array = np.power(image_array, gamma)
    image_array = (image_array * 255).astype(np.uint8)
    
    return Image.fromarray(image_array)


def remove_noise(image, method='gaussian', kernel_size=3):
    """
    去除图像噪声
    
    Args:
        image: PIL.Image 输入图像
        method: str 去噪方法 ('gaussian', 'median', 'bilateral')
        kernel_size: int 核大小
        
    Returns:
        PIL.Image: 去噪后的图像
    """
    image_array = np.array(image)
    
    if method == 'gaussian':
        result = cv2.GaussianBlur(image_array, (kernel_size, kernel_size), 0)
    elif method == 'median':
        result = cv2.medianBlur(image_array, kernel_size)
    elif method == 'bilateral':
        result = cv2.bilateralFilter(image_array, kernel_size, 75, 75)
    else:
        result = image_array
    
    return Image.fromarray(result)


def standardize_resolution(image, target_size=(224, 224)):
    """
    标准化图像分辨率
    
    Args:
        image: PIL.Image 输入图像
        target_size: tuple 目标尺寸
        
    Returns:
        PIL.Image: 标准化后的图像
    """
    return image.resize(target_size, Image.Resampling.LANCZOS)


def preprocess_image(image_path, target_size=(224, 224), use_clahe=False, normalize=True):
    """
    完整的图像预处理流程
    
    Args:
        image_path: str 图像文件路径
        target_size: tuple 目标尺寸
        use_clahe: bool 是否应用 CLAHE 增强
        normalize: bool 是否归一化
        
    Returns:
        numpy.ndarray: 预处理后的图像数组
    """
    # 1. 加载图像
    image = load_image(image_path)
    
    # 2. 调整大小并填充
    image = resize_and_pad(image, target_size)
    
    # 3. CLAHE 增强（可选）
    if use_clahe:
        image = apply_clahe(image)
    
    # 4. 归一化（可选）
    if normalize:
        return normalize_image(image)
    
    return np.array(image)


def analyze_image_properties(image_path):
    """
    分析图像属性（分辨率、文件大小等）
    
    Args:
        image_path: str 图像文件路径
        
    Returns:
        dict: 图像属性字典
    """
    try:
        with Image.open(image_path) as img:
            width, height = img.size
            mode = img.mode
            format = img.format
        
        file_size = os.path.getsize(image_path)
        
        return {
            'width': width,
            'height': height,
            'mode': mode,
            'format': format,
            'file_size_bytes': file_size,
            'file_size_mb': file_size / (1024 * 1024)
        }
    except Exception as e:
        print(f"分析图像属性失败: {image_path}, 错误: {e}")
        return None


def batch_preprocess_images(input_dir, output_dir, target_size=(224, 224), use_clahe=False):
    """
    批量预处理图像
    
    Args:
        input_dir: str 输入目录
        output_dir: str 输出目录
        target_size: tuple 目标尺寸
        use_clahe: bool 是否应用 CLAHE 增强
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    for img_file in input_path.glob("*.*"):
        if img_file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.bmp']:
            try:
                image = load_image(str(img_file))
                image = resize_and_pad(image, target_size)
                
                if use_clahe:
                    image = apply_clahe(image)
                
                output_file = output_path / img_file.name
                image.save(output_file)
                print(f"已处理: {img_file.name}")
            except Exception as e:
                print(f"处理失败: {img_file.name}, 错误: {e}")