# -*- coding: utf-8 -*-
"""
FastAPI 主入口 — 主业务服务 :8000
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import MAIN_SERVICE_PORT
from backend.database import init_db

# ─── Logger ───
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动/关闭生命周期"""
    logger.info('=' * 60)
    logger.info('主业务服务启动中...')
    logger.info('=' * 60)
    init_db()
    logger.info('数据库表已就绪')

    # 播种默认 admin
    from backend.api.auth import seed_admin
    from backend.database import SessionLocal
    db = SessionLocal()
    try:
        seed_admin(db)
        logger.info('默认 admin 用户已就绪')
    finally:
        db.close()

    logger.info(f'服务运行在 http://0.0.0.0:{MAIN_SERVICE_PORT}')
    yield
    logger.info('主业务服务关闭')


app = FastAPI(
    title='病虫害识别与RAG诊断系统 — 主服务',
    version='2.0.0',
    lifespan=lifespan,
)

# ─── CORS ───
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# ─── 注册路由 ───
from backend.api.auth import router as auth_router
from backend.api.users import router as users_router
from backend.api.model import router as model_router, experiments_router
from backend.api.rag import router as rag_router
from backend.api.detection import router as detection_router
from backend.api.knowledge_graph import router as kg_router
from backend.api.knowledge import router as knowledge_router
from backend.api.config import router as config_router
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(model_router)
app.include_router(experiments_router)
app.include_router(rag_router)
app.include_router(detection_router)
app.include_router(kg_router)
app.include_router(knowledge_router)
app.include_router(config_router)


@app.get('/api/health')
def health():
    return {'status': 'ok', 'service': 'main'}


if __name__ == '__main__':
    import uvicorn
    uvicorn.run('backend.main:app', host='0.0.0.0', port=MAIN_SERVICE_PORT, reload=True)
