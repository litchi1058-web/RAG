# 数据集说明

## 数据来源

### 1. 自有数据集
位置：`lsnet/data/data1/`

- **训练集**：`训练集/` 目录
- **测试集**：`测试集/` 目录
- **标签文件**：`labelname.xlsx`

### 2. PlantVillage 公开数据集
位置：`lsnet/data/plantvillage/`

## 类别定义

### 苹果类（5 类）
- Apple___Apple_scab （黑星病）
- Apple___Black_rot （黑腐病）
- Apple___Cedar_apple_rust （雪松锈病）
- Apple___healthy （健康）
- Apple___Powdery_mildew （白粉病）

### 樱桃类（3 类）
- Cherry_(including_sour)___Powdery_mildew （白粉病）
- Cherry_(including_sour)___healthy （健康）
- Cherry_(including_sour)___Black_rot （黑腐病）

## 数据划分比例

训练集 : 验证集 : 测试集 = 7 : 1 : 2

```
原始数据 → 合并（自有 + PlantVillage）→ 随机打乱 → 7:1:2 划分
```

## 使用方法

### 训练时自动划分
```bash
python lsnet/train.py --use-plantvillage
```

### 手动重新划分
```bash
python lsnet/tools/split_dataset.py \
  --source lsnet/data/data1 \
  --output lsnet/data/data_split \
  --train-ratio 0.7 --val-ratio 0.1 --test-ratio 0.2
```

### 数据分析
```bash
python lsnet/tools/analyze_dataset.py
```

输出内容：
- 每个类别的样本数量
- 图像分辨率分布
- 平均分辨率
- 总文件大小

### 下载 PlantVillage 苹果樱桃子集

1. **下载完整数据集**：
   - https://www.kaggle.com/datasets/mohitsingh1804/plantvillage
   - 约 2.5GB

2. **提取子集**：
```bash
python lsnet/tools/download_plantvillage.py --extract <path/to/plantvillage.zip>
```

3. **查看已下载数据**：
```bash
python lsnet/tools/download_plantvillage.py --info
```

## 数据增强

训练集采用：
- RandomHorizontalFlip
- RandomVerticalFlip
- RandomRotation (15°)
- ColorJitter
- RandomCrop
- ImageNet Normalization

验证/测试集只做 Resize + Normalization。
