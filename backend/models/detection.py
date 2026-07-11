# -*- coding: utf-8 -*-
"""
识别历史表 (detections)
"""
import datetime
from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Text

from backend.database import Base


class Detection(Base):
    __tablename__ = 'detections'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    image_url = Column(String(512), nullable=False)
    result = Column(Text, default='')                  # 识别结果（JSON 字符串）
    confidence = Column(Float, default=0.0)
    disease_name = Column(String(128), default='')      # 病害名称
    risk_level = Column(String(32), default='')          # 风险等级
    farmer_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    def __repr__(self):
        return f'<Detection {self.id} — {self.disease_name}>'
