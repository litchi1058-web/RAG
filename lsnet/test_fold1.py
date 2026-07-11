"""单独测试 Fold 1 模型"""
import sys
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import datasets, transforms
from pathlib import Path
import numpy as np
from sklearn.metrics import classification_report, confusion_matrix
import json

sys.path.insert(0, str(Path(__file__).parent))
from arch.lsnet import LSNet

def main():
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"设备: {device}")
    
    # 测试集路径
    test_dir = Path(__file__).parent / "data" / "custom" / "测试集"
    
    # 数据预处理
    transform = transforms.Compose([
        transforms.Resize((256, 256)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    test_dataset = datasets.ImageFolder(test_dir, transform=transform)
    test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False, num_workers=0)
    
    print(f"测试集: {len(test_dataset)} 张图片, {len(test_dataset.classes)} 类")
    print(f"类别: {test_dataset.classes}")
    
    # 加载 Fold 1 模型
    model_path = Path(__file__).parent / "models" / "lsnet_cv5_res256_20260619_231237" / "fold1" / "best_model.pth"
    print(f"\n加载模型: {model_path}")
    
    model = LSNet(num_classes=9)
    checkpoint = torch.load(model_path, map_location=device, weights_only=False)
    
    if 'model_state_dict' in checkpoint:
        model.load_state_dict(checkpoint['model_state_dict'])
        print(f"  Epoch: {checkpoint.get('epoch', 'N/A')}")
        print(f"  Best Val Acc: {checkpoint.get('best_acc', 'N/A')}")
    elif 'state_dict' in checkpoint:
        model.load_state_dict(checkpoint['state_dict'])
    else:
        model.load_state_dict(checkpoint)
    
    model.to(device)
    model.eval()
    
    # 评估
    all_preds = []
    all_labels = []
    all_probs = []
    
    with torch.no_grad():
        for images, labels in test_loader:
            images = images.to(device)
            outputs = model(images)
            probs = torch.softmax(outputs, dim=1)
            preds = outputs.argmax(dim=1)
            
            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(labels.numpy())
            all_probs.extend(probs.cpu().numpy())
    
    all_preds = np.array(all_preds)
    all_labels = np.array(all_labels)
    
    accuracy = (all_preds == all_labels).mean() * 100
    
    print(f"\n{'='*60}")
    print(f"Fold 1 模型测试结果")
    print(f"{'='*60}")
    print(f"测试准确率: {accuracy:.2f}%")
    
    # 分类报告
    print(f"\n分类报告:")
    report = classification_report(all_labels, all_preds, digits=4, target_names=test_dataset.classes)
    print(report)
    
    # 混淆矩阵
    cm = confusion_matrix(all_labels, all_preds)
    print(f"\n混淆矩阵:")
    print(cm)
    
    # 每个类别的准确率
    print(f"\n每个类别的准确率:")
    for i, cls in enumerate(test_dataset.classes):
        cls_mask = all_labels == i
        cls_correct = (all_preds[cls_mask] == i).sum()
        cls_total = cls_mask.sum()
        cls_acc = cls_correct / cls_total * 100 if cls_total > 0 else 0
        print(f"  {cls}: {cls_acc:.2f}% ({cls_correct}/{cls_total})")

if __name__ == "__main__":
    main()