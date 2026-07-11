# -*- coding: utf-8 -*-
"""
使用增强后的测试集评估所有实验模型
"""
import os
import sys
import json
from pathlib import Path
import torch
import numpy as np
from PIL import Image
from tqdm import tqdm

# 添加项目路径
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'lsnet'))
sys.path.insert(0, str(PROJECT_ROOT / 'backend'))

from arch import build_model
from sklearn.metrics import classification_report, confusion_matrix, f1_score, accuracy_score

# 图像归一化参数
IMG_MEAN = [0.485, 0.456, 0.406]
IMG_STD = [0.229, 0.224, 0.225]


class AugmentedTestEvaluator:
    """增强测试集评估器"""

    def __init__(self, test_dir, image_size=224, device='cuda'):
        """
        Args:
            test_dir: str 增强后的测试集路径
            image_size: int 图像尺寸
            device: str 设备类型
        """
        self.test_dir = Path(test_dir)
        self.image_size = image_size
        self.device = device if torch.cuda.is_available() else 'cpu'

        # 定义数据变换
        from torchvision import transforms
        self.transform = transforms.Compose([
            transforms.Resize((image_size + 32, image_size + 32)),
            transforms.CenterCrop(image_size),
            transforms.ToTensor(),
            transforms.Normalize(IMG_MEAN, IMG_STD),
        ])

    def load_dataset(self):
        """加载增强后的测试集"""
        from torch.utils.data import Dataset

        class TestDataset(Dataset):
            def __init__(self, root_dir, transform):
                self.root = Path(root_dir)
                self.transform = transform
                self.paths = []
                self.labels = []

                # 获取所有类别
                class_dirs = sorted([d for d in self.root.iterdir() if d.is_dir()])
                self.class_names = [d.name for d in class_dirs]

                # 加载所有图片
                for class_idx, class_dir in enumerate(class_dirs):
                    for img_path in class_dir.glob('*.jpg'):
                        self.paths.append(img_path)
                        self.labels.append(class_idx)
                    for img_path in class_dir.glob('*.png'):
                        self.paths.append(img_path)
                        self.labels.append(class_idx)

            def __len__(self):
                return len(self.paths)

            def __getitem__(self, idx):
                img = Image.open(self.paths[idx]).convert('RGB')
                img = self.transform(img)
                label = self.labels[idx]
                return img, label

        self.dataset = TestDataset(self.test_dir, self.transform)
        self.class_names = self.dataset.class_names

        from torch.utils.data import DataLoader
        self.loader = DataLoader(
            self.dataset,
            batch_size=32,
            shuffle=False,
            num_workers=0,
            pin_memory=True
        )

        return len(self.dataset), len(self.class_names)

    def load_model(self, model_path, model_name='lsnet', config=None):
        """
        加载模型

        Args:
            model_path: str 模型路径
            model_name: str 模型名称
            config: dict 配置参数

        Returns:
            model: torch.nn.Module 加载的模型
        """
        # 构建模型
        num_classes = len(self.class_names)
        model = build_model(model_name, num_classes=num_classes, pretrained=False)

        # 加载权重
        checkpoint = torch.load(model_path, map_location=self.device, weights_only=True)
        
        # 处理不同的检查点格式
        if 'model_state_dict' in checkpoint:
            state_dict = checkpoint['model_state_dict']
        elif 'model' in checkpoint:
            state_dict = checkpoint['model']
        else:
            state_dict = checkpoint
        
        model.load_state_dict(state_dict)
        model = model.to(self.device)
        model.eval()

        return model

    def evaluate(self, model):
        """
        评估模型

        Returns:
            dict: 评估结果
        """
        all_preds = []
        all_labels = []

        with torch.no_grad():
            for images, labels in tqdm(self.loader, desc="评估中"):
                images = images.to(self.device, non_blocking=True)
                labels = labels.to(self.device, non_blocking=True)

                with torch.amp.autocast('cuda'):
                    outputs = model(images)
                    _, preds = outputs.max(1)

                all_preds.extend(preds.cpu().numpy())
                all_labels.extend(labels.cpu().numpy())

        # 计算指标
        acc = accuracy_score(all_labels, all_preds) * 100.0
        f1 = f1_score(all_labels, all_preds, average='macro', zero_division=0) * 100.0

        # 生成分类报告
        report = classification_report(
            all_labels, all_preds,
            target_names=self.class_names,
            output_dict=True,
            zero_division=0
        )

        # 生成混淆矩阵
        cm = confusion_matrix(all_labels, all_preds)

        return {
            'accuracy': acc,
            'f1_score': f1,
            'classification_report': report,
            'confusion_matrix': cm.tolist(),
            'all_preds': all_preds,
            'all_labels': all_labels
        }


def find_best_models():
    """
    找出所有实验的最佳模型路径

    Returns:
        list: 实验信息列表
    """
    experiments = []
    results_dir = PROJECT_ROOT / 'lsnet' / 'results'
    models_dir = PROJECT_ROOT / 'lsnet' / 'models'

    # 遍历所有实验结果
    for exp_dir in sorted(results_dir.iterdir()):
        if not exp_dir.is_dir():
            continue

        # 读取实验结果
        cv_results_path = exp_dir / 'cv_results.json'
        if not cv_results_path.exists():
            continue

        with open(cv_results_path, 'r', encoding='utf-8') as f:
            cv_results = json.load(f)

        # 获取对应的模型路径
        exp_name = exp_dir.name
        model_dir = models_dir / exp_name

        if not model_dir.exists():
            continue

        best_model_path = model_dir / 'best_model.pth'
        if not best_model_path.exists():
            continue

        # 提取实验类型
        exp_suffix = cv_results['config'].get('exp_suffix', 'unknown')
        test_acc = cv_results.get('mean_test_acc', 0)
        test_f1 = cv_results.get('mean_test_f1', 0)

        experiments.append({
            'name': exp_name,
            'suffix': exp_suffix,
            'model_path': str(best_model_path),
            'config': cv_results['config'],
            'original_test_acc': test_acc,
            'original_test_f1': test_f1
        })

    return experiments


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='增强测试集模型评估工具')
    parser.add_argument('--test-dir', '-t', type=str,
                        default='d:/bf/proj/RAG/lsnet/data/custom/测试集_augmented',
                        help='增强后的测试集路径')
    parser.add_argument('--image-size', '-i', type=int, default=224,
                        help='图像尺寸')
    parser.add_argument('--output', '-o', type=str,
                        default='d:/bf/proj/RAG/lsnet/results/augmented_test_results',
                        help='结果输出目录')
    parser.add_argument('--device', '-d', type=str, default='cuda',
                        help='设备类型')

    args = parser.parse_args()

    # 创建输出目录
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("增强测试集模型评估工具")
    print("=" * 70)
    print(f"\n增强测试集: {args.test_dir}")
    print(f"图像尺寸: {args.image_size}")
    print(f"输出目录: {output_dir}")
    print()

    # 创建评估器
    evaluator = AugmentedTestEvaluator(
        test_dir=args.test_dir,
        image_size=args.image_size,
        device=args.device
    )

    # 加载数据集
    print("加载增强后的测试集...")
    num_samples, num_classes = evaluator.load_dataset()
    print(f"测试样本数: {num_samples}")
    print(f"类别数: {num_classes}")
    print(f"类别列表: {evaluator.class_names}")
    print()

    # 查找所有实验模型
    print("查找所有实验模型...")
    experiments = find_best_models()
    print(f"找到 {len(experiments)} 个实验模型\n")

    # 评估所有模型
    all_results = []
    print("开始评估所有模型...\n")

    for exp in tqdm(experiments, desc="评估模型"):
        print(f"\n评估: {exp['suffix']}")

        try:
            # 加载模型
            model = evaluator.load_model(
                model_path=exp['model_path'],
                model_name=exp['config'].get('model', 'lsnet'),
                config=exp['config']
            )

            # 评估
            result = evaluator.evaluate(model)
            result['experiment'] = exp['name']
            result['suffix'] = exp['suffix']
            result['original_test_acc'] = exp['original_test_acc']
            result['original_test_f1'] = exp['original_test_f1']
            result['config'] = exp['config']

            # 计算性能变化
            result['acc_change'] = result['accuracy'] - exp['original_test_acc']
            result['f1_change'] = result['f1_score'] - exp['original_test_f1']

            print(f"  增强测试集 - Acc: {result['accuracy']:.2f}%, F1: {result['f1_score']:.2f}%")
            print(f"  原始测试集 - Acc: {exp['original_test_acc']:.2f}%, F1: {exp['original_test_f1']:.2f}%")
            print(f"  变化       - Acc: {result['acc_change']:+.2f}%, F1: {result['f1_change']:+.2f}%")

            all_results.append(result)

        except Exception as e:
            print(f"  评估失败: {e}")
            continue

    # 按增强测试集准确率排序
    all_results.sort(key=lambda x: x['accuracy'], reverse=True)

    # 打印汇总结果
    print("\n" + "=" * 70)
    print("评估结果汇总（按增强测试集准确率排序）")
    print("=" * 70)
    print(f"\n{'排名':<4} {'实验名称':<30} {'增强Acc':<10} {'原始Acc':<10} {'变化':<8}")
    print("-" * 70)

    for i, result in enumerate(all_results, 1):
        change_symbol = "+" if result['acc_change'] >= 0 else ""
        print(f"{i:<4} {result['suffix']:<30} {result['accuracy']:.2f}%{'':<5} "
              f"{result['original_test_acc']:.2f}%{'':<5} "
              f"{change_symbol}{result['acc_change']:.2f}%")

    # 保存结果
    results_file = output_dir / 'augmented_test_results.json'
    with open(results_file, 'w', encoding='utf-8') as f:
        # 转换为可序列化格式
        serializable_results = []
        for result in all_results:
            r = {
                'experiment': result['experiment'],
                'suffix': result['suffix'],
                'accuracy': result['accuracy'],
                'f1_score': result['f1_score'],
                'original_test_acc': result['original_test_acc'],
                'original_test_f1': result['original_test_f1'],
                'acc_change': result['acc_change'],
                'f1_change': result['f1_change'],
                'config': result['config'],
                'class_names': evaluator.class_names
            }
            serializable_results.append(r)

        json.dump({
            'test_dataset': str(args.test_dir),
            'num_samples': num_samples,
            'num_classes': num_classes,
            'results': serializable_results
        }, f, ensure_ascii=False, indent=2)

    print(f"\n详细结果已保存至: {results_file}")

    # 生成对比分析报告
    print("\n" + "=" * 70)
    print("性能变化分析")
    print("=" * 70)

    improved = [r for r in all_results if r['acc_change'] > 0]
    decreased = [r for r in all_results if r['acc_change'] < 0]
    unchanged = [r for r in all_results if r['acc_change'] == 0]

    print(f"\n性能提升的模型: {len(improved)} 个")
    if improved:
        for r in improved[:5]:
            print(f"  - {r['suffix']}: {r['acc_change']:+.2f}%")

    print(f"\n性能下降的模型: {len(decreased)} 个")
    if decreased:
        for r in decreased[:5]:
            print(f"  - {r['suffix']}: {r['acc_change']:+.2f}%")

    print(f"\n性能不变的模型: {len(unchanged)} 个")

    print("\n" + "=" * 70)


if __name__ == '__main__':
    main()
