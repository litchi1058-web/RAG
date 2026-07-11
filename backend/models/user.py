# -*- coding: utf-8 -*-
"""
用户表 (users)
"""
import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum as SAEnum
import enum

from backend.database import Base


class UserRole(str, enum.Enum):
    ADMIN = 'admin'
    DATA_MANAGER = 'data_manager'
    FARMER = 'farmer'


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    password_hash = Column(String(128), nullable=False)
    role = Column(SAEnum(UserRole), nullable=False, default=UserRole.FARMER)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    is_active = Column(Integer, default=1)

    def __repr__(self):
        return f'<User {self.username} ({self.role.value})>'
