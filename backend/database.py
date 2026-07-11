# -*- coding: utf-8 -*-
"""
SQLAlchemy 引擎与会话
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from backend.config import DATABASE_URL

_is_sqlite = DATABASE_URL.startswith("sqlite")
_is_mysql = DATABASE_URL.startswith("mysql")
_is_postgresql = DATABASE_URL.startswith("postgresql")

_connect_args = {}
if _is_sqlite:
    _connect_args["check_same_thread"] = False
elif _is_mysql:
    _connect_args["charset"] = "utf8mb4"

engine = create_engine(
    DATABASE_URL,
    connect_args=_connect_args,
    pool_pre_ping=not _is_sqlite,
    pool_size=5 if _is_sqlite else 10,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI 依赖注入：获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """建表（测试/开发用，生产推荐 Alembic）"""
    from backend.models.user import User
    from backend.models.document import Document
    from backend.models.detection import Detection
    Base.metadata.create_all(bind=engine)
