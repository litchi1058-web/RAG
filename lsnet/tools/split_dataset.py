# -*- coding: utf-8 -*-
"""
数据集划分工具
将原始数据按 7:1:2 比例重新划分
"""
import os
import shutil
import random
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.shared.paths import get_raw_data_dir


def split_data(source_dir=None, output_dir=None, train_ratio=0.7, val_ratio=0.1, test_ratio=0.2, seed=42):
    """
    将数据按 7:1:2 比例划分为训练/验证/测试集
    """
    if source_dir is None:
        source_dir = get_raw_data_dir()

    if output_dir is None:
        output_dir = source_dir.parent / "data_split"

    random.seed(seed)
    source_path = Path(source_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    for split in ['train', 'val', 'test']:
        for d in source_path.iterdir():
            if d.is_dir():
                (output_path / split / d.name).mkdir(parents=True, exist_ok=True)

    total_train, total_val, total_test = 0, 0, 0

    for class_dir in source_path.iterdir():
        if not class_dir.is_dir():
            continue

        images = [f for f in class_dir.iterdir() if f.suffix.lower() in ['.jpg', '.jpeg', '.png']]
        random.shuffle(images)

        n = len(images)
        train_end = int(n * train_ratio)
        val_end = train_end + int(n * val_ratio)

        train_imgs = images[:train_end]
        val_imgs = images[train_end:val_end]
        test_imgs = images[val_end:]

        for img in train_imgs:
            shutil.copy2(img, output_path / "train" / class_dir.name / img.name)
        for img in val_imgs:
            shutil.copy2(img, output_path / "val" / class_dir.name / img.name)
        for img in test_imgs:
            shutil.copy2(img, output_path / "test" / class_dir.name / img.name)

        total_train += len(train_imgs)
        total_val += len(val_imgs)
        total_test += len(test_imgs)

        print(f"{class_dir.name}: train={len(train_imgs)}, val={len(val_imgs)}, test={len(test_imgs)}")

    print(f"\n总计: train={total_train}, val={total_val}, test={total_test}")
    print(f"输出目录: {output_path}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='数据集划分')
    parser.add_argument('--source', type=str, default=None)
    parser.add_argument('--output', type=str, default=None)
    parser.add_argument('--train-ratio', type=float, default=0.7)
    parser.add_argument('--val-ratio', type=float, default=0.1)
    parser.add_argument('--test-ratio', type=float, default=0.2)
    args = parser.parse_args()

    split_data(
        source_dir=args.source,
        output_dir=args.output,
        train_ratio=args.train_ratio,
        val_ratio=args.val_ratio,
        test_ratio=args.test_ratio
    )
