# -*- coding: utf-8 -*-
"""
用户管理 API（仅 admin）
GET    /api/users        → 用户列表
POST   /api/users        → 新增用户
PUT    /api/users/{id}   → 编辑用户
DELETE /api/users/{id}   → 删除用户
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from backend.database import get_db
from backend.models.user import User, UserRole
from backend.api.deps import get_current_user

router = APIRouter(prefix='/api/users', tags=['用户管理'])
pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

# ─── Schemas ───

class CreateUserRequest(BaseModel):
    username: str = Field(min_length=2, max_length=64)
    password: str = Field(min_length=4, max_length=128)
    role: UserRole = UserRole.FARMER

class UpdateUserRequest(BaseModel):
    username: str | None = Field(None, min_length=2, max_length=64)
    password: str | None = Field(None, min_length=4, max_length=128)
    role: UserRole | None = None
    is_active: int | None = None


def admin_required(user: User = Depends(get_current_user)):
    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail='仅管理员可执行此操作')
    return user


@router.get('')
def list_users(db: Session = Depends(get_db), _=Depends(admin_required)):
    """获取所有用户列表"""
    users = db.query(User).order_by(User.created_at.desc()).all()
    return [
        {
            'id': u.id,
            'username': u.username,
            'role': u.role.value,
            'is_active': bool(u.is_active),
            'created_at': u.created_at.isoformat() if u.created_at else '',
        }
        for u in users
    ]


@router.post('')
def create_user(req: CreateUserRequest, db: Session = Depends(get_db),
                _=Depends(admin_required)):
    """新增用户"""
    existing = db.query(User).filter(User.username == req.username).first()
    if existing:
        raise HTTPException(status_code=400, detail='用户名已存在')

    user = User(
        username=req.username,
        password_hash=pwd_context.hash(req.password),
        role=req.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {
        'success': True,
        'user': {
            'id': user.id,
            'username': user.username,
            'role': user.role.value,
            'is_active': True,
            'created_at': user.created_at.isoformat() if user.created_at else '',
        }
    }


@router.put('/{user_id}')
def update_user(user_id: int, req: UpdateUserRequest,
                db: Session = Depends(get_db), _=Depends(admin_required)):
    """编辑用户"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail='用户不存在')

    if req.username is not None:
        existing = db.query(User).filter(
            User.username == req.username, User.id != user_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail='用户名已被使用')
        user.username = req.username
    if req.password is not None:
        user.password_hash = pwd_context.hash(req.password)
    if req.role is not None:
        user.role = req.role
    if req.is_active is not None:
        user.is_active = req.is_active

    db.commit()
    db.refresh(user)
    return {
        'success': True,
        'user': {
            'id': user.id,
            'username': user.username,
            'role': user.role.value,
            'is_active': bool(user.is_active),
            'created_at': user.created_at.isoformat() if user.created_at else '',
        }
    }


@router.delete('/{user_id}')
def delete_user(user_id: int, db: Session = Depends(get_db),
                _=Depends(admin_required)):
    """删除用户（不允许删除 admin）"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail='用户不存在')
    if user.username == 'admin':
        raise HTTPException(status_code=403, detail='不允许删除 admin 用户')

    db.delete(user)
    db.commit()
    return {'success': True, 'message': '用户已删除'}