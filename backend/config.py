# -*- coding: utf-8 -*-
"""
应用配置 — JWT密钥、数据库连接、服务端口
"""
import os
from pathlib import Path
from urllib.parse import quote_plus

PROJECT_ROOT = Path(__file__).resolve().parent.parent

env_path = PROJECT_ROOT / '.env'
if env_path.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(dotenv_path=env_path, override=True)
        print(f'Loaded .env from {env_path}')
    except ImportError:
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
        print(f'Loaded .env manually from {env_path}')

# ─── Neo4j ───
NEO4J_ENABLED = os.environ.get('NEO4J_ENABLED', 'true').lower() in ('1', 'true', 'yes')
NEO4J_URI = os.environ.get('NEO4J_URI', 'neo4j://127.0.0.1:7687')
NEO4J_USER = os.environ.get('NEO4J_USER', 'neo4j')
NEO4J_PASSWORD = os.environ.get('NEO4J_PASSWORD', 'Litchii1!')

# ─── JWT ───
SECRET_KEY = os.environ.get('SECRET_KEY', 'change-this-to-a-random-secret-in-production')
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 480

# ─── Database ───
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = int(os.environ.get('DB_PORT', 3306))
DB_USER = os.environ.get('DB_USER', 'rag_admin')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'rag_pass_2024')
DB_NAME = os.environ.get('DB_NAME', 'rag_db')
DB_TYPE = os.environ.get('DB_TYPE', 'sqlite').lower()

if DB_TYPE == 'mysql':
    DATABASE_URL = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4'
elif DB_TYPE == 'postgresql':
    encoded_password = quote_plus(DB_PASSWORD)
    DATABASE_URL = f'postgresql+psycopg2://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
else:
    SQLITE_PATH = PROJECT_ROOT / 'backend' / 'rag.db'
    DATABASE_URL = f'sqlite:///{SQLITE_PATH}'

# ─── Service ports ───
MAIN_SERVICE_PORT = int(os.environ.get('MAIN_SERVICE_PORT', 8000))
AI_SERVICE_PORT = int(os.environ.get('AI_SERVICE_PORT', 8001))
NGINX_PORT = int(os.environ.get('NGINX_PORT', 8080))

# ─── File paths ───
UPLOAD_DIR = PROJECT_ROOT / 'backend' / 'uploads'
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR = PROJECT_ROOT / 'backend' / 'logs'
LOG_DIR.mkdir(parents=True, exist_ok=True)

# ─── AI service URL ───
AI_SERVICE_URL = os.environ.get('AI_SERVICE_URL', f'http://localhost:{AI_SERVICE_PORT}')

# ─── LLM (Qwen / llama-cpp) ───
QWEN_API_KEY = os.environ.get('QWEN_API_KEY', '')
QWEN_API_URL = os.environ.get('QWEN_API_URL', 'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions')
QWEN_MODEL = os.environ.get('QWEN_MODEL', 'qwen-plus')
LLM_MODEL_PATH = os.environ.get('LLM_MODEL_PATH', str(PROJECT_ROOT / 'qwen2-1_5b-instruct-q4_k_m.gguf'))
LLM_USE_LOCAL = os.environ.get('LLM_USE_LOCAL', 'true').lower() in ('1', 'true', 'yes')

# ─── Default admin seed ───
DEFAULT_ADMIN_USERNAME = 'admin'
DEFAULT_ADMIN_PASSWORD = 'admin123'
