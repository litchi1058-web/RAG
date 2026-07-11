# 🍎 RAG 智能病害诊断系统

基于 RAG（检索增强生成）技术的苹果/樱桃病害智能诊断系统，采用 LSNet 轻量级网络进行图像识别，Qwen2-1.5B（GGUF 量化）进行自然语言生成。

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Vue](https://img.shields.io/badge/Vue-3.4+-green.svg)](https://vuejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-orange.svg)](https://fastapi.tiangolo.com/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-red.svg)](https://pytorch.org/)

## ✨ 功能特性

| 模块 | 功能描述 |
|------|---------|
| **图像识别** | 基于 LSNet 的苹果/樱桃病害识别（9类），支持 GPU 加速 |
| **智能问答** | 基于本地 GGUF 模型的 RAG 检索增强问答 |
| **知识图谱** | 病害、症状、药剂的图结构知识库（181节点，136关系） |
| **知识管理** | 结构化知识库的增删改查管理 |
| **诊断记录** | 历史诊断记录查询与统计 |
| **用户管理** | 三种角色权限（管理员、数据管理员、农户） |

## 🛠️ 技术栈

- **后端**: FastAPI, Uvicorn, SQLAlchemy, PostgreSQL/SQLite
- **前端**: Vue 3, Vite, Element Plus, Pinia, vis-network
- **AI 服务**: PyTorch, LSNet, llama-cpp-python (GGUF)
- **图像识别**: LSNet-CBAM（轻量级网络）
- **LLM**: Qwen2-1.5B-Instruct（GGUF Q4_K_M 量化）

## 📦 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- PostgreSQL 15+（或使用 SQLite）

### 1. 克隆项目

```bash
git clone https://github.com/your-username/rag-disease-diagnosis.git
cd rag-disease-diagnosis
```

### 2. 安装依赖

```bash
# 后端依赖
pip install -r backend/requirements.txt

# 前端依赖
cd frontend
npm install
cd ..
```

### 3. 配置环境

复制 `.env.example` 为 `.env` 并修改配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
# 数据库配置（支持 sqlite/mysql/postgresql）
DB_TYPE=postgresql
DB_HOST=localhost
DB_PORT=5432
DB_USER=your_user
DB_PASSWORD=your_password
DB_NAME=rag_db

# JWT 密钥（生产环境务必修改）
SECRET_KEY=your-random-secret-key

# 服务端口
MAIN_SERVICE_PORT=8000
AI_SERVICE_PORT=8001
```

### 4. 下载模型

下载 LSNet 模型权重和 GGUF 模型文件，放置到项目根目录：

- LSNet 模型: `lsnet/models/best_model.pth`
- GGUF 模型: `qwen2-1_5b-instruct-q4_k_m.gguf`

### 5. 启动服务

**方法一：一键启动（Windows）**

```bash
scripts/start-all.bat
```

**方法二：手动启动**

```bash
# 终端1: AI 服务（加载 GGUF 模型）
set PYTHONPATH=%cd%
python ai_service/main.py

# 终端2: 后端 API
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000

# 终端3: 前端
cd frontend
npm run dev -- --port 5174
```

### 6. 访问系统

- **前端**: http://localhost:5174
- **后端 API**: http://localhost:8000/docs
- **AI 服务**: http://localhost:8001/ai/health

### 默认账号

| 用户名 | 密码 | 角色 |
|--------|------|------|
| admin | admin123 | 管理员 |
| man | 123456 | 数据管理员 |
| farmer | 123456 | 农户 |

## 📁 项目结构

```
rag-disease-diagnosis/
├── .github/workflows/       # CI/CD 配置
├── ai_service/              # AI 推理服务（端口8001）
│   └── main.py              # 加载 LSNet 和 GGUF 模型
├── backend/                 # 后端 API 服务（端口8000）
│   ├── api/                 # REST API 路由
│   ├── models/              # SQLAlchemy ORM 模型
│   ├── data/                # 知识库数据文件
│   ├── shared/              # 共享常量和配置
│   ├── uploads/             # 上传文件存储
│   ├── config.py            # 配置管理
│   ├── database.py          # 数据库连接
│   └── main.py              # FastAPI 入口
├── frontend/                # 前端项目
│   ├── src/
│   │   ├── views/           # 页面组件
│   │   ├── api/             # API 调用封装
│   │   ├── stores/          # Pinia 状态管理
│   │   └── router/          # Vue Router 配置
│   └── package.json
├── lsnet/                   # LSNet 模型实现
│   ├── arch/                # 网络架构
│   ├── data/                # 训练数据集
│   ├── experiments/         # 实验脚本
│   └── tools/               # 工具脚本
├── docs/                    # 项目文档
├── diagrams/                # 架构图（Mermaid）
├── deploy/                  # 部署配置（Nginx）
├── scripts/                 # 启动脚本和工具
│   ├── start-all.bat        # Windows 一键启动
│   ├── start-backend.bat    # 后端启动
│   ├── start-frontend.bat   # 前端启动
│   └── start.bat            # 完整启动脚本
├── tests/                   # 测试文件
│   ├── test_ai_predict.py   # AI 预测测试
│   ├── test_backend_api.py  # 后端 API 测试
│   ├── test_user_management.py  # 用户管理测试
│   └── test_full_predict.py # 完整预测测试
├── .env.example             # 环境变量模板
├── .gitignore               # Git 忽略规则
├── LICENSE                  # MIT 许可证
└── README.md                # 项目主页
```

## 🚀 API 文档

启动后端服务后访问：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 核心接口

| 接口 | 方法 | 描述 |
|------|------|------|
| `/api/auth/login` | POST | 用户登录 |
| `/api/auth/register` | POST | 用户注册（仅管理员） |
| `/api/rag/query` | POST | RAG 问答查询 |
| `/api/model/predict` | POST | 图像病害识别 |
| `/api/knowledge` | GET | 获取知识库列表 |
| `/api/knowledge-graph` | GET | 获取知识图谱 |

## 📊 数据集

- **苹果/樱桃病害**: 6类病害 + 3类健康
- **数据划分**: 7:1:2（训练/验证/测试）
- **PlantVillage 公开数据集集成**

## 🔧 开发

### 前端开发

```bash
cd frontend
npm run dev          # 开发模式
npm run build        # 生产构建
npm run preview      # 预览构建结果
```

### 后端开发

```bash
# 自动重载模式
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

# 测试 API
python _test_backend_api.py
```

## 📝 文档

- [架构设计](docs/ARCHITECTURE.md)
- [API 文档](docs/API.md)
- [数据集说明](docs/DATASET.md)
- [部署指南](docs/DEPLOYMENT.md)

## 📄 License

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 🙏 致谢

- [LSNet](https://github.com/whai362/LSNet) - 轻量级语义分割网络
- [Qwen2](https://github.com/QwenLM/Qwen2) - 阿里巴巴通义千问
- [llama-cpp-python](https://github.com/abetlen/llama-cpp-python) - GGUF 模型推理
- [PlantVillage](https://plantvillage.psu.edu/) - 植物病害数据集

---

⭐ 如果这个项目对你有帮助，请给个 Star！
