# -*- coding: utf-8 -*-
"""
LSNet 数据集模块
数据预处理和数据增强的独立板块
"""
from .dataset import (
    FruitDiseaseDataset,
    CustomDataset,
    collect_all_samples,
    split_dataset,
    split_dataset_stratified,
    load_plantvillage_data,
    load_custom_dataset,
    load_custom_samples,
    merge_datasets,
    get_class_distribution,
    calculate_class_weights
)
from .transforms import (
    get_train_transform,
    get_val_transform,
    get_strong_transform,
    get_simple_transform,
    get_transforms,
    create_mixed_transform,
    RandomGaussianNoise,
    RandomCutout,
    CustomResize
)
from .preprocessing import (
    load_image,
    resize_and_pad,
    normalize_image,
    apply_clahe,
    adjust_gamma,
    remove_noise,
    standardize_resolution,
    preprocess_image,
    analyze_image_properties,
    batch_preprocess_images
)
from .augmentation import (
    mixup_data,
    mixup_criterion,
    cutmix_data,
    cutout,
    random_erase,
    random_rotation,
    random_flip,
    random_crop,
    random_color_jitter,
    random_grayscale,
    random_resized_crop,
    AugmentationPipeline
)
from .analyzer import analyze_dataset

__all__ = [
    # 数据集类
    'FruitDiseaseDataset',
    'CustomDataset',
    
    # 数据集加载与处理
    'collect_all_samples',
    'split_dataset',
    'split_dataset_stratified',
    'load_plantvillage_data',
    'load_custom_dataset',
    'load_custom_samples',
    'merge_datasets',
    'get_class_distribution',
    'calculate_class_weights',
    
    # 变换函数
    'get_train_transform',
    'get_val_transform',
    'get_strong_transform',
    'get_simple_transform',
    'get_transforms',
    'create_mixed_transform',
    'RandomGaussianNoise',
    'RandomCutout',
    'CustomResize',
    
    # 预处理工具
    'load_image',
    'resize_and_pad',
    'normalize_image',
    'apply_clahe',
    'adjust_gamma',
    'remove_noise',
    'standardize_resolution',
    'preprocess_image',
    'analyze_image_properties',
    'batch_preprocess_images',
    
    # 增强技术
    'mixup_data',
    'mixup_criterion',
    'cutmix_data',
    'cutout',
    'random_erase',
    'random_rotation',
    'random_flip',
    'random_crop',
    'random_color_jitter',
    'random_grayscale',
    'random_resized_crop',
    'AugmentationPipeline',
    
    # 分析工具
    'analyze_dataset'
]