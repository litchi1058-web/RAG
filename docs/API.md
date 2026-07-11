# API 文档

## 基础地址
```
http://127.0.0.1:5000/api
```

## 通用响应格式

```json
{
  "success": true,
  "data": {},
  "message": "操作成功"
}
```

## 1. 认证接口

### POST /api/login
登录

**请求体：**
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**响应：**
```json
{
  "success": true,
  "user": { "username": "admin" },
  "message": "登录成功"
}
```

### POST /api/logout
登出

### GET /api/auth/status
检查登录状态

## 2. 知识管理

### GET /api/knowledge
获取所有病害知识

### GET /api/knowledge/{key}
获取单个病害

### POST /api/knowledge
添加病害

**请求体：**
```json
{
  "disease_key": "苹果_黑星病_一般",
  "disease_name": "苹果黑星病",
  "crop_type": "苹果",
  "disease_type": "真菌性病害",
  "risk_level": "中等",
  "symptoms": ["症状1", "症状2"],
  "causes": ["原因1"],
  "treatment": ["方法1"],
  "prevention": ["措施1"]
}
```

### PUT /api/knowledge/{key}
更新病害

### DELETE /api/knowledge/{key}
删除病害

## 3. 知识图谱

### GET /api/knowledge-graph
获取知识图谱数据

**响应：**
```json
{
  "success": true,
  "data": {
    "nodes": [
      { "id": "苹果_黑星病_一般", "name": "苹果黑星病(一般)", "category": "disease" }
    ],
    "links": [
      { "source": "苹果_黑星病_一般", "target": "crop_苹果", "relation": "BELONGS_TO" }
    ]
  }
}
```

### POST /api/knowledge-graph/rebuild
重建知识图谱

## 4. 模型管理

### GET /api/model/status
获取所有模型状态

### GET /api/model/logs?limit=50
获取训练日志

### GET /api/model/metrics
获取模型评估指标

### POST /api/model/predict
模型推理（multipart/form-data 上传图片）

## 5. 数据管理

### GET /api/dataset/stats
获取数据集统计

### GET /api/dataset/distribution
获取类别分布

### POST /api/dataset/upload
上传数据集文件

## 6. 诊断记录

### GET /api/diagnosis/history?page=1&limit=20
获取诊断历史（分页）

### GET /api/diagnosis/{id}
获取诊断详情

### POST /api/diagnosis
添加诊断记录

### DELETE /api/diagnosis/{id}
删除诊断记录

## 7. 系统设置

### GET /api/config
获取系统配置

### PUT /api/config
更新系统配置

### POST /api/config/reset
重置配置

### GET /api/system/info
获取系统信息（Python版本、CUDA状态等）
