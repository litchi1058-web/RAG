# -*- coding: utf-8 -*-
"""
共享配置模块
后端服务和 LSNet 训练共用
"""
import os
from pathlib import Path

# ==================== 项目路径 ====================
# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent

# 子模块路径
BACKEND_DIR = BASE_DIR / "backend"
FRONTEND_DIR = BASE_DIR / "frontend"
LSNET_DIR = BASE_DIR / "lsnet"
DATA_DIR = BASE_DIR / "lsnet" / "data"
DOCS_DIR = BASE_DIR / "docs"
SCRIPTS_DIR = BASE_DIR / "scripts"

# ==================== 数据路径 ====================
# 原始数据集
RAW_DATA_DIR = LSNET_DIR / "data" / "data1"
TRAIN_DIR = RAW_DATA_DIR / "训练集"
TEST_DIR = RAW_DATA_DIR / "测试集"
LABEL_FILE = RAW_DATA_DIR / "labelname.xlsx"

# PlantVillage 数据集
PLANTVILLAGE_DIR = LSNET_DIR / "data" / "plantvillage"

# 模型输出
CHECKPOINTS_DIR = LSNET_DIR / "checkpoints"
LOGS_DIR = LSNET_DIR / "logs"
RESULTS_DIR = LSNET_DIR / "results"

# ==================== 模型配置 ====================
# 类别定义
APPLE_CLASSES = [
    'Apple___Apple_scab',
    'Apple___Black_rot',
    'Apple___Cedar_apple_rust',
    'Apple___healthy',
    'Apple___Powdery_mildew'
]

CHERRY_CLASSES = [
    'Cherry_(including_sour)___Powdery_mildew',
    'Cherry_(including_sour)___healthy',
    'Cherry_(including_sour)___Black_rot'
]

PLANTVILLAGE_CLASSES = APPLE_CLASSES + CHERRY_CLASSES

# 数据集划分比例
TRAIN_RATIO = 0.7
VAL_RATIO = 0.1
TEST_RATIO = 0.2

# 训练参数
DEFAULT_BATCH_SIZE = 32
DEFAULT_EPOCHS = 80
DEFAULT_LR = 1e-3
DEFAULT_WEIGHT_DECAY = 1e-4

# 图像参数
IMAGE_SIZE = 224
IMG_MEAN = [0.485, 0.456, 0.406]
IMG_STD = [0.229, 0.224, 0.225]

# ==================== API 配置 ====================
API_HOST = "0.0.0.0"
API_PORT = 5000
API_PREFIX = "/api"
FRONTEND_PORT = 5173

# ==================== 后端数据文件 ====================
KNOWLEDGE_BASE_FILE = BACKEND_DIR / "data" / "knowledge_base.json"
DIAGNOSIS_HISTORY_FILE = BACKEND_DIR / "data" / "diagnosis_history.json"
SYSTEM_CONFIG_FILE = BACKEND_DIR / "data" / "system_config.json"
KNOWLEDGE_GRAPH_FILE = BACKEND_DIR / "data" / "knowledge_graph.json"

# ==================== 工具函数 ====================
def ensure_dir(path):
    """确保目录存在"""
    Path(path).mkdir(parents=True, exist_ok=True)

def to_path(path_str):
    """转换为 Path 对象"""
    return Path(path_str)
