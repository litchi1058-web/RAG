# RAG 智能病害诊断系统

基于 RAG（检索增强生成）技术的苹果/樱桃病害智能诊断系统。

## 项目结构

```
d:\bf\proj\RAG\
├── backend/                  # 后端服务（Flask + Python）
├── frontend/admin-web/       # 前端项目（Vue 3 + Vite + Element Plus）
├── lsnet/                    # 图像识别模型（PyTorch）
├── shared/                   # 共享配置
├── vgg/                      # VGG 参考实现（仅参考）
├── docs/                     # 项目文档
└── scripts/                  # 启动脚本
```

## 核心功能

| 模块 | 功能描述 |
|------|---------|
| 图像识别 | 基于 LSNet 的苹果/樱桃病害识别（9类） |
| 知识图谱 | 病害、症状、治疗方法的图结构知识库 |
| RAG 检索 | 基于知识库的检索增强生成 |
| 后台管理 | 知识库、模型、数据集、诊断记录管理 |
| 数据训练 | 支持多种模型架构对比实验 |

## 快速开始

### 1. 安装依赖

```bash
# 后端依赖
pip install -r backend/requirements.txt

# LSNet 训练依赖
pip install -r lsnet/requirements.txt

# 前端依赖
cd frontend/admin-web
npm install
```

### 2. 启动后端

```bash
python scripts/start_backend.py
# 访问 http://127.0.0.1:5000
# 默认账号：admin / admin123
```

### 3. 启动前端

```bash
python scripts/start_frontend.py
# 访问 http://127.0.0.1:5173
```

### 4. 训练模型

```bash
# 使用 LSNet + PlantVillage 数据集
python scripts/train_model.py lsnet --use-plantvillage

# 使用 MobileNetV2 对比
python scripts/train_model.py mobilenetv2 --use-plantvillage
```

## 数据集

- 苹果/樱桃病害数据：6类病害 + 3类健康
- 数据划分：7:1:2（训练/验证/测试）
- PlantVillage 公开数据集集成（苹果 + 樱桃子集）

## 技术栈

- **后端**: Flask, Python 3.11
- **前端**: Vue 3, Vite, Element Plus, ECharts, vis-network
- **模型**: PyTorch, LSNet / MobileNetV2 / EfficientNetB0
- **存储**: JSON 文件（可扩展为数据库）

## 文档

- [架构设计](ARCHITECTURE.md)
- [API 文档](API.md)
- [数据集说明](DATASET.md)
- [部署指南](DEPLOYMENT.md)
- [目录结构说明](../DIRECTORY_STRUCTURE.md)

## License

仅供学习和研究使用
