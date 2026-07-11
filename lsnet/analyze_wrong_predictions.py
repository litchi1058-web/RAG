"""分析误判样本的置信度"""
import sys
import torch
from torch.utils.data import DataLoader
from torchvision import datasets, transforms
from pathlib import Path
import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
from arch.lsnet import LSNet

def analyze_wrong_predictions():
    """分析误判样本"""
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    test_dir = Path(__file__).parent / "data" / "custom" / "测试集"
    transform = transforms.Compose([
        transforms.Resize((256, 256)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    test_dataset = datasets.ImageFolder(test_dir, transform=transform)
    test_loader = DataLoader(test_dataset, batch_size=1, shuffle=False, num_workers=0)
    
    # 加载 Fold 1 模型
    model_path = Path(__file__).parent / "models" / "lsnet_cv5_res256_20260619_231237" / "fold1" / "best_model.pth"
    model = LSNet(num_classes=9)
    checkpoint = torch.load(model_path, map_location=device, weights_only=False)
    model.load_state_dict(checkpoint['model_state_dict'])
    model.to(device)
    model.eval()
    
    print("="*60)
    print("误判样本分析")
    print("="*60)
    
    wrong_samples = []
    
    with torch.no_grad():
        for idx, (image, label) in enumerate(test_loader):
            image = image.to(device)
            output = model(image)
            probs = torch.softmax(output, dim=1)
            pred = output.argmax(dim=1).item()
            confidence = probs[0, pred].item()
            true_label = label.item()
            
            if pred != true_label:
                img_path = test_dataset.samples[idx][0]
                wrong_samples.append({
                    'path': img_path,
                    'true_label': true_label,
                    'pred_label': pred,
                    'confidence': confidence,
                    'all_probs': probs[0].cpu().numpy()
                })
    
    print(f"\n误判样本数: {len(wrong_samples)}")
    print(f"\n误判详情:")
    
    for sample in wrong_samples:
        print(f"\n  图片: {Path(sample['path']).name}")
        print(f"    真实标签: {sample['true_label']}")
        print(f"    预测标签: {sample['pred_label']}")
        print(f"    预测置信度: {sample['confidence']:.4f}")
        print(f"    各类别概率:")
        probs = sample['all_probs']
        for i, p in enumerate(probs):
            if p > 0.05:  # 只显示概率 > 5% 的类别
                print(f"      类别 {i}: {p:.4f}")
        
        # 低置信度警告
        if sample['confidence'] < 0.7:
            print(f"    ⚠️ 低置信度! 可能样本本身模糊或标注错误")
    
    # 统计误判分布
    print(f"\n{'='*60}")
    print(f"误判分布:")
    from collections import Counter
    true_labels = [s['true_label'] for s in wrong_samples]
    pred_labels = [s['pred_label'] for s in wrong_samples]
    
    for true, pred in zip(true_labels, pred_labels):
        print(f"  真实 {true} -> 预测 {pred}")
    
    # 置信度统计
    confidences = [s['confidence'] for s in wrong_samples]
    print(f"\n误判样本置信度:")
    print(f"  平均: {np.mean(confidences):.4f}")
    print(f"  最小: {np.min(confidences):.4f}")
    print(f"  最大: {np.max(confidences):.4f}")
    
    low_confidence = sum(1 for c in confidences if c < 0.7)
    print(f"  低置信度(<0.7): {low_confidence}/{len(confidences)}")
    
    if low_confidence > len(confidences) * 0.5:
        print(f"\n⚠️ 超过一半误判样本置信度较低，可能存在标注问题!")

if __name__ == "__main__":
    analyze_wrong_predictions()