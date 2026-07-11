"""测试知识蒸馏训练的模型"""
import sys
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import datasets, transforms
from pathlib import Path
import numpy as np
from sklearn.metrics import classification_report, confusion_matrix
import json

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from arch.lsnet import LSNet

def load_model(model_path, device):
    """加载模型"""
    model = LSNet(num_classes=9)
    checkpoint = torch.load(model_path, map_location=device, weights_only=False)
    
    # 处理不同的checkpoint格式
    if 'model_state_dict' in checkpoint:
        model.load_state_dict(checkpoint['model_state_dict'])
    elif 'state_dict' in checkpoint:
        model.load_state_dict(checkpoint['state_dict'])
    else:
        model.load_state_dict(checkpoint)
    
    model.to(device)
    model.eval()
    return model

def evaluate_model(model, test_loader, device):
    """评估模型"""
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
    report = classification_report(all_labels, all_preds, digits=4)
    cm = confusion_matrix(all_labels, all_preds)
    
    return accuracy, report, cm, all_preds, all_labels

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
    
    # 模型目录
    model_dir = Path(__file__).parent / "models" / "lsnet_cv5_res256_20260619_231237"
    
    # 测试各个模型
    models_to_test = [
        ("Final Model", model_dir / "final" / "final_model.pth"),
        ("Fold 1 (93.18%)", model_dir / "fold1" / "best_model.pth"),
        ("Fold 2 (89.77%)", model_dir / "fold2" / "best_model.pth"),
        ("Fold 3 (90.91%)", model_dir / "fold3" / "best_model.pth"),
        ("Fold 4 (93.18%)", model_dir / "fold4" / "best_model.pth"),
        ("Fold 5 (90.91%)", model_dir / "fold5" / "best_model.pth"),
    ]
    
    results = []
    
    print("\n" + "="*60)
    print("测试知识蒸馏训练的模型")
    print("="*60)
    
    for name, model_path in models_to_test:
        if not model_path.exists():
            print(f"\n{name}: 模型文件不存在")
            continue
        
        print(f"\n{name}:")
        model = load_model(model_path, device)
        accuracy, report, cm, preds, labels = evaluate_model(model, test_loader, device)
        
        print(f"  测试准确率: {accuracy:.2f}%")
        print(f"  分类报告:")
        print(report)
        
        results.append({
            "name": name,
            "accuracy": accuracy,
            "model_path": str(model_path)
        })
    
    # 保存结果
    results_file = Path(__file__).parent / "results" / "lsnet_cv5_res256_20260619_231237" / "test_results.json"
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n结果保存至: {results_file}")
    
    # 找出最佳模型
    best_result = max(results, key=lambda x: x['accuracy'])
    print(f"\n最佳模型: {best_result['name']}")
    print(f"最佳准确率: {best_result['accuracy']:.2f}%")

if __name__ == "__main__":
    main()