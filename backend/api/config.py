# -*- coding: utf-8 -*-
"""
系统配置 API — 读写 JSON 配置文件
"""
import json
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Depends

from backend.api.deps import get_current_user
from backend.models.user import User

router = APIRouter(prefix='/api/config', tags=['系统配置'])

# ─── 配置文件路径 ───
_CONFIG_DIR = Path(__file__).resolve().parent.parent / 'data'
_CONFIG_FILE = _CONFIG_DIR / 'config.json'

# ─── 默认配置 ───
DEFAULT_CONFIG: Dict[str, Any] = {
    'system_name': '病虫害识别与RAG诊断系统',
    'system_version': '2.0.0',
    'model_config': {
        'default_model': 'LSNet-CBAM',
        'confidence_threshold': 0.7,
        'enable_rag': True,
    },
    'data_config': {
        'use_plantvillage': True,
        'train_ratio': 0.7,
        'val_ratio': 0.15,
        'test_ratio': 0.15,
    },
}


def _ensure_config_dir():
    """确保配置目录存在"""
    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def _load_config() -> Dict[str, Any]:
    """从文件加载配置，文件不存在时返回默认配置"""
    _ensure_config_dir()
    if _CONFIG_FILE.exists():
        try:
            with open(_CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return dict(DEFAULT_CONFIG)


def _save_config(config: Dict[str, Any]):
    """保存配置到文件"""
    _ensure_config_dir()
    with open(_CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


@router.get('')
async def load_config(current_user: User = Depends(get_current_user)):
    """加载系统配置"""
    return _load_config()


@router.put('')
async def save_config(data: Dict[str, Any], current_user: User = Depends(get_current_user)):
    """保存系统配置"""
    _save_config(data)
    return {'success': True, 'config': data}
