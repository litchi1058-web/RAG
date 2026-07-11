# -*- coding: utf-8 -*-
"""
项目常量定义
"""
# ==================== 病害常量 ====================
# 风险等级
RISK_LEVELS = ['无', '低', '中等', '高']

# 病害类型
DISEASE_TYPES = [
    '真菌性病害',
    '细菌性病害',
    '病毒性病害',
    '线虫病害',
    '健康状态'
]

# 作物类型
CROP_TYPES = ['苹果', '樱桃']

# ==================== 状态常量 ====================
# 诊断状态
DIAGNOSIS_STATUS = {
    'PENDING': '待处理',
    'PROCESSED': '已处理',
    'COMPLETED': '已完成',
    'FAILED': '失败'
}

# 模型状态
MODEL_STATUS = {
    'UNTRAINED': '未训练',
    'TRAINING': '训练中',
    'TRAINED': '已训练',
    'FAILED': '训练失败'
}

# ==================== 默认用户 ====================
DEFAULT_ADMIN = {
    'username': 'admin',
    'password': 'admin123'  # 生产环境应使用加密存储
}

# ==================== 病害严重程度 ====================
SEVERITY_LEVELS = ['一般', '严重']

# ==================== 知识图谱关系类型 ====================
KG_RELATIONSHIPS = {
    'BELONGS_TO': '属于',           # 病害 → 作物
    'CAUSED_BY': '病因',            # 病害 → 病因
    'HAS_SYMPTOM': '症状',          # 病害 → 症状
    'TREATED_BY': '治疗方法',       # 病害 → 治疗
    'PREVENTED_BY': '预防措施',     # 病害 → 预防
    'SIMILAR_TO': '相似',           # 病害 ↔ 病害
}

# 知识图谱节点类别
KG_CATEGORIES = {
    'crop': '作物',
    'disease': '病害',
    'disease_type': '病害类型',
    'symptom': '症状',
    'treatment': '治疗',
    'cause': '成因',
    'prevention': '预防',
    'chemical': '药剂',
    'severity': '严重程度',
    'risk_level': '风险等级',
}

# 扩展的知识图谱关系类型
KG_RELATIONSHIPS_EXTENDED = {
    'BELONGS_TO': '属于',
    'CAUSED_BY': '病因',
    'HAS_SYMPTOM': '症状',
    'TREATED_BY': '治疗方法',
    'PREVENTED_BY': '预防措施',
    'SIMILAR_TO': '相似病害',
    'HAS_CAUSE': '成因',
    'USES_CHEMICAL': '推荐药剂',
    'HAS_SEVERITY': '严重程度',
    'HAS_RISK': '风险等级',
    'RELATED_TO': '相关',
}

# ==================== 图像与模型常量 ====================
# 输入图像尺寸
IMG_SIZE = 224

# ImageNet 预训练模型使用的均值/标准差
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]
IMG_MEAN = IMAGENET_MEAN
IMG_STD = IMAGENET_STD

# 支持的病害类别（与 lsnet/data/custom/labelname.xlsx 一致）
# 索引顺序: 0-健康, 1-黑星病一般, 2-黑星病严重, 3-黑斑病一般, 4-雪松锈病一般, 5-雪松锈病严重, 6-樱桃健康, 7-樱桃白粉病一般, 8-樱桃白粉病严重
CLASS_NAMES = [
    'Apple___healthy',
    'Apple___Apple_scab_normal',
    'Apple___Apple_scab_severe',
    'Apple___Black_rot',
    'Apple___Cedar_apple_rust_normal',
    'Apple___Cedar_apple_rust_severe',
    'Cherry_(including_sour)___healthy',
    'Cherry_(including_sour)___Powdery_mildew_normal',
    'Cherry_(including_sour)___Powdery_mildew_severe',
]

# 显示用的中文名称映射（与 labelname.xlsx 一致，用于前端展示）
CLASS_NAME_CN = {
    'Apple___healthy': '苹果健康',
    'Apple___Apple_scab_normal': '苹果黑星病',
    'Apple___Apple_scab_severe': '苹果黑星病（严重）',
    'Apple___Black_rot': '苹果黑斑病',
    'Apple___Cedar_apple_rust_normal': '苹果雪松锈病',
    'Apple___Cedar_apple_rust_severe': '苹果雪松锈病（严重）',
    'Cherry_(including_sour)___healthy': '樱桃健康',
    'Cherry_(including_sour)___Powdery_mildew_normal': '樱桃白粉病',
    'Cherry_(including_sour)___Powdery_mildew_severe': '樱桃白粉病（严重）',
}

# RAG知识库键名映射（用于在COMPLETE_KNOWLEDGE_BASE中查找匹配）
CLASS_NAME_RAG_KEY = {
    'Apple___healthy': '苹果_健康',
    'Apple___Apple_scab_normal': '苹果_黑星病_一般',
    'Apple___Apple_scab_severe': '苹果_黑星病_严重',
    'Apple___Black_rot': '苹果_黑斑病_一般',
    'Apple___Cedar_apple_rust_normal': '苹果_雪松锈病_一般',
    'Apple___Cedar_apple_rust_severe': '苹果_雪松锈病_严重',
    'Cherry_(including_sour)___healthy': '樱桃_健康',
    'Cherry_(including_sour)___Powdery_mildew_normal': '樱桃_白粉病_一般',
    'Cherry_(including_sour)___Powdery_mildew_severe': '樱桃_白粉病_严重',
}

# 支持的模型架构
SUPPORTED_MODELS = [
    'lsnet',           # 自研 LSNet（轻量级）
    'mobilenetv2',     # MobileNetV2
    'shufflenetv2',    # ShuffleNetV2
    'efficientnetb0',  # EfficientNet-B0
]
