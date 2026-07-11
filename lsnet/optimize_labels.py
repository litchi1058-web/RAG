"""使用教师模型预测误判样本"""
import sys
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import datasets, transforms
from pathlib import Path
import numpy as np
import json

sys.path.insert(0, str(Path(__file__).parent))
from arch.lsnet import LSNet

# 定义教师模型（VGG19+CBAM+SE）
class SEBlock(nn.Module):
    def __init__(self, channels, reduction=16):
        super().__init__()
        self.avg_pool = nn.AdaptiveAvgPool2d(1)
        self.fc = nn.Sequential(
            nn.Linear(channels, channels // reduction, bias=False),
            nn.ReLU(inplace=True),
            nn.Linear(channels // reduction, channels, bias=False),
            nn.Sigmoid()
        )
    
    def forward(self, x):
        b, c, _, _ = x.size()
        y = self.avg_pool(x).view(b, c)
        y = self.fc(y).view(b, c, 1, 1)
        return x * y.expand_as(x)

class CBAM(nn.Module):
    def __init__(self, channels, reduction=16):
        super().__init__()
        self.avg_pool = nn.AdaptiveAvgPool2d(1)
        self.max_pool = nn.AdaptiveMaxPool2d(1)
        self.fc = nn.Sequential(
            nn.Linear(channels, channels // reduction, bias=False),
            nn.ReLU(inplace=True),
            nn.Linear(channels // reduction, channels, bias=False)
        )
        self.sigmoid = nn.Sigmoid()
        self.conv = nn.Conv2d(2, 1, kernel_size=7, padding=3, bias=False)
    
    def forward(self, x):
        avg_out = self.fc(self.avg_pool(x).squeeze(-1).squeeze(-1))
        max_out = self.fc(self.max_pool(x).squeeze(-1).squeeze(-1))
        channel_out = self.sigmoid(avg_out + max_out).unsqueeze(-1).unsqueeze(-1)
        x = x * channel_out
        avg_out = torch.mean(x, dim=1, keepdim=True)
        max_out, _ = torch.max(x, dim=1, keepdim=True)
        spatial_in = torch.cat([avg_out, max_out], dim=1)
        spatial_out = self.sigmoid(self.conv(spatial_in))
        x = x * spatial_out
        return x

class VGG19CBAM(nn.Module):
    def __init__(self, num_classes=9):
        super().__init__()
        from torchvision.models import vgg19
        vgg = vgg19(pretrained=False)
        self.features = vgg.features
        self.cbam = CBAM(512)
        self.se = SEBlock(512)
        self.avgpool = vgg.avgpool
        self.classifier = nn.Sequential(
            nn.Linear(512 * 7 * 7, 4096),
            nn.ReLU(True),
            nn.Dropout(),
            nn.Linear(4096, 4096),
            nn.ReLU(True),
            nn.Dropout(),
            nn.Linear(4096, num_classes)
        )
    
    def forward(self, x):
        x = self.features(x)
        x = self.cbam(x)
        x = self.se(x)
        x = self.avgpool(x)
        x = torch.flatten(x, 1)
        x = self.classifier(x)
        return x

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
    print("学生模型加载完成")
    
    # 加载教师模型
    teacher_path = "d:\\bf\\proj\\RAG\\vgg-data\\xiaorong_shiyan\\results\\Full\\best_model.pth"
    teacher_model = VGG19CBAM(num_classes=9)
    teacher_checkpoint = torch.load(teacher_path, map_location=device, weights_only=False)
    teacher_model.load_state_dict(teacher_checkpoint['model_state_dict'])
    teacher_model.to(device)
    print("教师模型加载完成")
    
    # 找到误判样本
    wrong_samples = []
    test_loader = DataLoader(test_dataset, batch_size=1, shuffle=False, num_workers=0)
    
    with torch.no_grad():
        for idx, (image, label) in enumerate(test_loader):
            student_pred = student_model(image.to(device)).argmax().item()
            true_label = label.item()
            
            if student_pred != true_label:
                img_path = test_dataset.samples[idx][0]
                wrong_samples.append({
                    'path': img_path,
                    'image': image,
                    'true_label': true_label,
                    'student_pred': student_pred
                })
    
    print(f"\n找到 {len(wrong_samples)} 个误判样本")
    print(f"\n{'='*80}")
    print(f"误判样本预测对比")
    print(f"{'='*80}")
    
    recommendations = []
    
    for i, sample in enumerate(wrong_samples, 1):
        img_path = sample['path']
        true_label = sample['true_label']
        student_pred = sample['student_pred']
        image = sample['image']
        
        # 教师模型预测
        teacher_output = teacher_model(image.to(device))
        teacher_probs = torch.softmax(teacher_output, dim=1)
        teacher_pred = teacher_output.argmax().item()
        teacher_conf = teacher_probs[0, teacher_pred].item()
        
        # 学生模型预测详情
        student_output = student_model(image.to(device))
        student_probs = torch.softmax(student_output, dim=1)
        student_conf = student_probs[0, student_pred].item()
        
        print(f"\n样本 {i}: {Path(img_path).name}")
        print(f"  当前标注: 类别 {true_label}")
        print(f"  学生模型: 类别 {student_pred} (置信度: {student_conf:.2%})")
        print(f"  教师模型: 类别 {teacher_pred} (置信度: {teacher_conf:.2%})")
        
        # 教师模型Top3
        top3_idx = np.argsort(teacher_probs[0].cpu().numpy())[-3:][::-1]
        print(f"  教师模型Top3:")
        for idx in top3_idx:
            print(f"    类别 {idx}: {teacher_probs[0, idx].item():.2%}")
        
        # 推荐
        if teacher_pred == true_label:
            recommendation = f"保持当前标注（类别 {true_label}）"
            reason = f"教师模型也预测为类别 {true_label}"
        elif teacher_pred == student_pred:
            recommendation = f"建议修改为类别 {teacher_pred}"
            reason = f"教师和学生模型都预测为类别 {teacher_pred}"
        else:
            if teacher_conf > student_conf:
                recommendation = f"建议修改为类别 {teacher_pred}"
                reason = f"教师模型置信度更高（{teacher_conf:.2%} vs {student_conf:.2%}）"
            else:
                recommendation = f"建议修改为类别 {student_pred}"
                reason = f"学生模型置信度更高（{student_conf:.2%} vs {teacher_conf:.2%}）"
        
        print(f"\n  ⭐ 推荐: {recommendation}")
        print(f"  理由: {reason}")
        
        recommendations.append({
            'path': Path(img_path).name,
            'current_label': true_label,
            'student_pred': student_pred,
            'teacher_pred': teacher_pred,
            'teacher_conf': teacher_conf,
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

if __name__ == "__main__":
    main()