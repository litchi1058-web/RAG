# -*- coding: utf-8 -*-
"""
认证 API — bcrypt + JWT
POST /api/auth/login     登录
POST /api/auth/register  注册（仅admin）
GET  /api/auth/me        当前用户信息
"""
import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import jwt, JWTError

from backend.database import get_db
from backend.models.user import User, UserRole
from backend.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from backend.api.deps import get_current_user

router = APIRouter(prefix='/api/auth', tags=['认证'])

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

# ─── Pydantic schemas ───

class LoginRequest(BaseModel):
    username: str = Field(min_length=2, max_length=64)
    password: str = Field(min_length=4, max_length=128)

class RegisterRequest(BaseModel):
    username: str = Field(min_length=2, max_length=64)
    password: str = Field(min_length=4, max_length=128)
    role: UserRole = UserRole.FARMER

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = 'bearer'
    user: dict

class UserInfo(BaseModel):
    id: int
    username: str
    role: UserRole
    created_at: str

# ─── Helpers ───

def create_access_token(data: dict) -> str:
    expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {**data, 'exp': expire}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def seed_admin(db: Session):
    """首次启动时创建默认 admin（幂等）"""
    existing = db.query(User).filter(User.username == 'admin').first()
    if existing:
        return
    from backend.config import DEFAULT_ADMIN_USERNAME, DEFAULT_ADMIN_PASSWORD
    admin = User(
        username=DEFAULT_ADMIN_USERNAME,
        password_hash=pwd_context.hash(DEFAULT_ADMIN_PASSWORD),
        role=UserRole.ADMIN,
    )
    db.add(admin)
    db.commit()

# ─── Routes ───

@router.post('/login', response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """用户登录 → JWT token"""
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not pwd_context.verify(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail='用户名或密码错误')
    if not user.is_active:
        raise HTTPException(status_code=403, detail='账户已被禁用')

    token = create_access_token({'sub': str(user.id), 'role': user.role.value})
    return TokenResponse(
        access_token=token,
        user={
            'id': user.id,
            'username': user.username,
            'role': user.role.value,
        }
    )


@router.post('/register')
def register(req: RegisterRequest, db: Session = Depends(get_db),
             current_user: User = Depends(get_current_user)):
    """注册新用户（仅 admin）"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail='仅管理员可注册用户')

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
    return {'success': True, 'user': {'id': user.id, 'username': user.username, 'role': user.role.value}}


class PublicRegisterRequest(BaseModel):
    username: str = Field(min_length=2, max_length=64)
    password: str = Field(min_length=4, max_length=128)
    email: str = Field(default='')


@router.post('/register/public')
def public_register(req: PublicRegisterRequest, db: Session = Depends(get_db)):
    """公开注册（普通用户）"""
    existing = db.query(User).filter(User.username == req.username).first()
    if existing:
        raise HTTPException(status_code=400, detail='用户名已存在')

    user = User(
        username=req.username,
        password_hash=pwd_context.hash(req.password),
        role=UserRole.FARMER,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {'success': True, 'message': '注册成功', 'user': {'id': user.id, 'username': user.username, 'role': user.role.value}}


@router.get('/me')
def get_me(current_user: User = Depends(get_current_user)):
    """获取当前登录用户信息"""
    return {
        'id': current_user.id,
        'username': current_user.username,
        'role': current_user.role.value,
        'created_at': current_user.created_at.isoformat() if current_user.created_at else '',
    }
