# -*- coding: utf-8 -*-
"""
路径管理模块
统一管理项目中的所有路径
"""
import os
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# ==================== 后端路径 ====================
def get_backend_dir():
    return PROJECT_ROOT / "backend"

def get_backend_data_dir():
    """后端数据目录"""
    path = PROJECT_ROOT / "backend" / "data"
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_uploads_dir():
    """上传文件目录"""
    path = PROJECT_ROOT / "backend" / "uploads"
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_logs_dir():
    """日志目录"""
    path = PROJECT_ROOT / "backend" / "logs"
    path.mkdir(parents=True, exist_ok=True)
    return path

# ==================== LSNet 路径 ====================
def get_lsnet_dir():
    return PROJECT_ROOT / "lsnet"

def get_data_dir():
    """LSNet 数据目录"""
    path = PROJECT_ROOT / "lsnet" / "data"
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_raw_data_dir():
    """原始数据目录（自定义数据集）"""
    return PROJECT_ROOT / "lsnet" / "data" / "custom"

def get_plantvillage_dir():
    """PlantVillage 数据集目录"""
    path = PROJECT_ROOT / "lsnet" / "data" / "plantvillage"
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_checkpoints_dir():
    """模型权重目录（训练好的参数 + 预训练权重）"""
    path = PROJECT_ROOT / "lsnet" / "models"
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_train_logs_dir():
    """训练日志目录"""
    path = PROJECT_ROOT / "lsnet" / "logs"
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_results_dir():
    """实验结果目录"""
    path = PROJECT_ROOT / "lsnet" / "results"
    path.mkdir(parents=True, exist_ok=True)
    return path

# ==================== 前端路径 ====================
def get_frontend_dir():
    return PROJECT_ROOT / "frontend"

def get_admin_web_dir():
    return PROJECT_ROOT / "frontend" / "admin-web"
