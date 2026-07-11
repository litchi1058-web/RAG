# 部署指南

## 开发环境部署

### 1. 环境要求
- Python 3.10+
- Node.js 16+
- PyTorch 1.10+ (CPU/GPU 均可)

### 2. 后端启动

```bash
# 安装依赖
pip install -r backend/requirements.txt
pip install -r lsnet/requirements.txt

# 启动后端
python scripts/start_backend.py
```

### 3. 前端启动

```bash
# 安装依赖
cd frontend/admin-web
npm install

# 开发模式
npm run dev
# 或
python scripts/start_frontend.py

# 生产构建
npm run build
```

## 生产环境部署

### 1. 使用 Gunicorn 部署后端

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 'backend.app:app'
```

### 2. 前端构建并用 Nginx 服务

```bash
cd frontend/admin-web
npm run build
# 产物在 dist/ 目录
```

Nginx 配置示例：
```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端
    location / {
        root /path/to/frontend/admin-web/dist;
        try_files $uri $uri/ /index.html;
    }

    # 后端 API
    location /api/ {
        proxy_pass http://127.0.0.1:5000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 3. 使用 Docker

创建 `Dockerfile.backend`:
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY backend/requirements.txt lsnet/requirements.txt ./
RUN pip install -r requirements.txt -r ../lsnet/requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "backend.app:app"]
```

创建 `Dockerfile.frontend`:
```dockerfile
FROM node:18-alpine as build
WORKDIR /app
COPY frontend/admin-web/ ./
RUN npm install && npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
```

## 训练流程

### 1. 准备数据
```bash
# 分析现有数据
python lsnet/tools/analyze_dataset.py

# 下载 PlantVillage 子集（可选）
python lsnet/tools/download_plantvillage.py --guide
```

### 2. 训练模型
```bash
# LSNet + PlantVillage
python lsnet/train.py --model lsnet --use-plantvillage --epochs 80

# MobileNetV2 对比实验
python lsnet/train.py --model mobilenetv2 --use-plantvillage --epochs 80
```

### 3. 查看结果
- 训练日志：`lsnet/logs/`
- 模型权重：`lsnet/checkpoints/best_model.pth`
- 实验结果：`lsnet/results/`

## 常见问题

### Q1: 启动后端报 ModuleNotFoundError
检查 `shared/` 目录是否在 Python 路径中。在 `backend/app.py` 顶部已添加 `sys.path.insert(0, PROJECT_ROOT)`。

### Q2: 前端无法连接后端
检查 Vite 代理配置（`vite.config.js`）和后端是否正常运行。

### Q3: PlantVillage 数据集下载慢
建议使用国内镜像或代理。

### Q4: CUDA 不可用
代码会自动回退到 CPU，但训练会变慢。
