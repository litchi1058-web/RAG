# -*- coding: utf-8 -*-
"""
知识库 CRUD API — 基于 COMPLETE_KNOWLEDGE_BASE 的内存 CRUD
"""
import copy
import re
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Depends

from backend.api.deps import get_current_user
from backend.api.rag import COMPLETE_KNOWLEDGE_BASE
from backend.models.user import User

router = APIRouter(prefix='/api/knowledge', tags=['知识库管理'])

# ─── 从 COMPLETE_KNOWLEDGE_BASE 加载到内存副本 ───
_knowledge_store: Dict[str, Dict[str, Any]] = copy.deepcopy(COMPLETE_KNOWLEDGE_BASE)


def _generate_key(disease_name: str) -> str:
    """从 disease_name 自动生成 key，如 '樱桃白粉病（轻度初发期）' → '樱桃_白粉病_一般'"""
    # 尝试匹配已有的命名模式
    name = disease_name.strip()
    # 移除括号内的描述
    base = re.sub(r'[（(][^)）]*[)）]', '', name).strip()
    # 常见病害名称映射
    disease_keywords = ['黑星病', '黑斑病', '白粉病', '锈病', '炭疽病', '褐斑病',
                        '灰斑病', '花叶病', '腐烂病', '链格孢枯萎病', '雪松锈病',
                        '轮纹病', '斑点落叶病', '霉心病', '锈果病',
                        '褐腐病', '叶斑病', '流胶病', '根腐病', '穿孔病']
    found_disease = ''
    for kw in disease_keywords:
        if kw in base:
            found_disease = kw
            break

    # 提取作物名（病害之前的部分）
    crop = base.replace(found_disease, '').strip() if found_disease else '未知'

    # 严重程度
    severity = '一般'
    if '严重' in name or '重度' in name:
        severity = '严重'
    elif '健康' in name:
        severity = '健康'

    key = f'{crop}_{found_disease}_{severity}' if found_disease else name.replace(' ', '_')
    return key


def _ensure_key_unique(base_key: str) -> str:
    """确保 key 唯一，冲突时加数字后缀"""
    key = base_key
    counter = 1
    while key in _knowledge_store:
        key = f'{base_key}_{counter}'
        counter += 1
    return key


@router.get('')
async def list_knowledge(current_user: User = Depends(get_current_user)):
    """获取全部知识条目，以 dict (keyed by disease_key) 形式返回"""
    return _knowledge_store


@router.get('/{key}')
async def get_knowledge(key: str, current_user: User = Depends(get_current_user)):
    """获取单条知识条目"""
    if key not in _knowledge_store:
        raise HTTPException(status_code=404, detail=f'知识条目 "{key}" 不存在')
    return _knowledge_store[key]


@router.post('')
async def create_knowledge(data: Dict[str, Any], current_user: User = Depends(get_current_user)):
    """创建新的知识条目，自动生成 key"""
    if 'disease_name' not in data or not data['disease_name']:
        raise HTTPException(status_code=400, detail='disease_name 为必填项')

    base_key = _generate_key(data['disease_name'])
    key = _ensure_key_unique(base_key)

    if key in _knowledge_store:
        raise HTTPException(status_code=409, detail=f'知识条目 "{key}" 已存在')

    # 确保所有列表字段为 list
    list_fields = ['causes', 'symptoms', 'immediate_measures', 'recommended_chemicals',
                   'treatment_plan', 'precautions', 'cultivation_measures', 'monitoring_plan',
                   'long_term_measures', 'personal_protection', 'environmental_protection',
                   'food_safety']
    for field in list_fields:
        if field not in data or not isinstance(data[field], list):
            data[field] = data.get(field, [])

    # 确保字符串字段存在
    str_fields = ['disease_name', 'severity', 'risk_level', 'urgency', 'infectivity',
                  'diagnosis_summary', 'region_suggest', 'weather_suggest']
    for field in str_fields:
        if field not in data:
            data[field] = data.get(field, '')

    _knowledge_store[key] = data
    return {'key': key, 'disease_name': data['disease_name']}


@router.put('/{key}')
async def update_knowledge(key: str, data: Dict[str, Any], current_user: User = Depends(get_current_user)):
    """更新已有的知识条目"""
    if key not in _knowledge_store:
        raise HTTPException(status_code=404, detail=f'知识条目 "{key}" 不存在')

    entry = _knowledge_store[key]
    for k, v in data.items():
        entry[k] = v
    _knowledge_store[key] = entry
    return {'key': key, 'disease_name': entry.get('disease_name', '')}


@router.delete('/{key}')
async def delete_knowledge(key: str, current_user: User = Depends(get_current_user)):
    """删除知识条目"""
    if key not in _knowledge_store:
        raise HTTPException(status_code=404, detail=f'知识条目 "{key}" 不存在')

    del _knowledge_store[key]
    return {'success': True, 'key': key}
