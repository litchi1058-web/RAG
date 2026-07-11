# -*- coding: utf-8 -*-
"""
识别记录 API
GET    /api/detection/history  → 识别历史记录
POST   /api/detection          → 保存识别记录
GET    /api/detection/{id}     → 识别记录详情
DELETE /api/detection/{id}     → 删除识别记录
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List
from pydantic import BaseModel

from backend.database import get_db
from backend.models.detection import Detection
from backend.models.user import User
from backend.api.deps import get_current_user

router = APIRouter(prefix='/api/detection', tags=['识别记录'])


@router.get('/history')
async def get_detection_history(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Detection)
    if current_user.role.value == 'farmer':
        query = query.filter(Detection.farmer_id == current_user.id)
    total = query.count()
    records = query.order_by(desc(Detection.created_at)).offset((page - 1) * limit).limit(limit).all()
    
    return {
        'data': [
            {
                'id': r.id,
                'image_url': r.image_url,
                'disease_name': r.disease_name,
                'confidence': r.confidence,
                'risk_level': r.risk_level,
                'result': r.result,
                'created_at': r.created_at.isoformat() if r.created_at else '',
            }
            for r in records
        ],
        'total': total,
        'page': page,
        'limit': limit
    }


class CreateDetectionRequest(BaseModel):
    image_url: str = ''
    result: str = ''
    confidence: float = 0.0
    disease_name: str = ''
    risk_level: str = ''


@router.post('')
async def create_detection(
    data: CreateDetectionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    detection = Detection(
        image_url=data.image_url,
        result=data.result,
        confidence=data.confidence,
        disease_name=data.disease_name,
        risk_level=data.risk_level,
        farmer_id=current_user.id if current_user.role.value == 'farmer' else None,
    )
    db.add(detection)
    db.commit()
    db.refresh(detection)

    return {
        'success': True,
        'id': detection.id,
        'message': '识别记录已保存'
    }


@router.get('/{detection_id}')
async def get_detection_detail(
    detection_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    detection = db.query(Detection).filter(Detection.id == detection_id).first()
    if not detection:
        raise HTTPException(status_code=404, detail='记录不存在')
    
    if current_user.role.value == 'farmer' and detection.farmer_id != current_user.id:
        raise HTTPException(status_code=403, detail='无权访问')
    
    return {
        'id': detection.id,
        'image_url': detection.image_url,
        'disease_name': detection.disease_name,
        'confidence': detection.confidence,
        'risk_level': detection.risk_level,
        'result': detection.result,
        'created_at': detection.created_at.isoformat() if detection.created_at else '',
    }


@router.delete('/{detection_id}')
async def delete_detection(
    detection_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    detection = db.query(Detection).filter(Detection.id == detection_id).first()
    if not detection:
        raise HTTPException(status_code=404, detail='记录不存在')
    
    if current_user.role.value == 'farmer' and detection.farmer_id != current_user.id:
        raise HTTPException(status_code=403, detail='无权删除')
    
    db.delete(detection)
    db.commit()
    
    return {'success': True, 'message': '记录已删除'}
