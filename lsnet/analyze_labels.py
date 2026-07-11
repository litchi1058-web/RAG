"""分析误判样本并给出标签建议"""
import sys
import torch
from torch.utils.data import DataLoader
from torchvision import datasets, transforms
from pathlib import Path
import numpy as np
import json
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
from arch.lsnet import LSNet

def main():
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"设备: {device}")
    
    test_dir = Path(__file__).parent / "data" / "custom" / "测试集"
    transform = transforms.Compose([
        transforms.Resize((256, 256)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    test_dataset = datasets.ImageFolder(test_dir, transform=transform)
    
    # 加载学生模型
    student_path = Path(__file__).parent / "models" / "lsnet_cv5_res256_20260619_231237" / "fold1" / "best_model.pth"
    student_model = LSNet(num_classes=9)
    student_checkpoint = torch.load(student_path, map_location=device, weights_only=False)
    student_model.load_state_dict(student_checkpoint['model_state_dict'])
    student_model.to(device)
    student_model.eval()  # 设置为评估模式
    print("学生模型加载完成 (测试准确率 94.32%)")
    
    # 找到误判样本
    wrong_samples = []
    test_loader = DataLoader(test_dataset, batch_size=1, shuffle=False, num_workers=0)
    
    with torch.no_grad():
        for idx, (image, label) in enumerate(test_loader):
            output = student_model(image.to(device))
            probs = torch.softmax(output, dim=1)
            pred = output.argmax().item()
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
    
    print(f"\n找到 {len(wrong_samples)} 个误判样本")
    print(f"\n{'='*80}")
    print(f"误判样本分析与标签建议")
    print(f"{'='*80}")
    
    recommendations = []
    
    for i, sample in enumerate(wrong_samples, 1):
        img_path = sample['path']
        true_label = sample['true_label']
        pred_label = sample['pred_label']
        confidence = sample['confidence']
        probs = sample['all_probs']
        
        print(f"\n样本 {i}: {Path(img_path).name}")
        print(f"  当前标注: 类别 {true_label}")
        print(f"  模型预测: 类别 {pred_label} (置信度: {confidence:.2%})")
        
        # 显示Top3预测
        top3_idx = np.argsort(probs)[-3:][::-1]
        print(f"  模型Top3预测:")
        for idx in top3_idx:
            print(f"    类别 {idx}: {probs[idx]:.2%}")
        
        # 分析和建议
        print(f"\n  分析:")
        
        # 检查是否低置信度
        if confidence < 0.7:
            print(f"    ⚠️ 预测置信度较低({confidence:.2%})，样本可能模糊或标注错误")
            recommendation = f"建议人工复核图片 {Path(img_path).name}"
            reason = f"模型预测置信度低，无法确定正确标签"
        elif probs[true_label] > 0.3:
            print(f"    ℹ️ 模型对当前标注也有一定置信度({probs[true_label]:.2%})")
            print(f"    ℹ️ 样本可能处于类别边界，标注可能正确")
            recommendation = f"保持当前标注（类别 {true_label}）"
            reason = f"模型对当前标注也有一定置信度，样本可能模糊"
        else:
            print(f"    ⚠️ 模型对当前标注置信度很低({probs[true_label]:.2%})")
            print(f"    ℹ️ 模型强烈认为应该是类别 {pred_label}")
            recommendation = f"建议修改为类别 {pred_label}"
            reason = f"模型对预测类别置信度高({confidence:.2%})，对当前标注置信度低"
        
        print(f"\n  ⭐ 推荐: {recommendation}")
        print(f"  理由: {reason}")
        
        recommendations.append({
            'path': Path(img_path).name,
            'current_label': int(true_label),
            'pred_label': int(pred_label),
            'confidence': float(confidence),
            'current_label_prob': float(probs[true_label]),
            'recommendation': recommendation,
            'reason': reason
        })
    
    # 保存结果
    result_file = Path(__file__).parent / "results" / "lsnet_cv5_res256_20260619_231237" / "label_recommendations.json"
    result_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(recommendations, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*80}")
    print(f"推荐结果已保存至: {result_file}")
    print(f"{'='*80}")
    
    # 总结
    print(f"\n总结:")
    low_conf_count = sum(1 for r in recommendations if r['confidence'] < 0.7)
    high_conf_wrong = sum(1 for r in recommendations if r['confidence'] >= 0.7)
    
    print(f"  低置信度误判(<70%): {low_conf_count} 个 - 建议人工复核")
    print(f"  高置信度误判(>=70%): {high_conf_wrong} 个 - 可能标注错误")
    
    if low_conf_count > 0:
        print(f"\n低置信度误判样本:")
        for r in recommendations:
            if r['confidence'] < 0.7:
                print(f"  - {r['path']}")

if __name__ == "__main__":
    main()