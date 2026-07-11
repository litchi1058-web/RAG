# -*- coding: utf-8 -*-
"""
PlantVillage 数据集下载工具
"""
import os
import sys
import tarfile
import zipfile
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.shared.paths import get_plantvillage_dir
from backend.shared.constants import APPLE_CLASSES, CHERRY_CLASSES, PLANTVILLAGE_CLASSES

WANTED_CLASSES = set(PLANTVILLAGE_CLASSES)


def download_from_kaggle():
    """显示下载指南"""
    print("=" * 60)
    print("PlantVillage 数据集下载指南")
    print("=" * 60)
    print()
    print("1. 访问以下链接下载完整数据集（约 2.5GB）：")
    print("   https://www.kaggle.com/datasets/mohitsingh1804/plantvillage")
    print()
    print("2. 将压缩包放到任意位置")
    print()
    print("3. 运行本脚本提取苹果和樱桃子集：")
    print('   python download_plantvillage.py --extract <path>')
    print()


def extract_apple_cherry(archive_path, output_dir=None):
    """
    从完整数据集中提取苹果和樱桃子集
    """
    if output_dir is None:
        output_dir = get_plantvillage_dir()

    print("=" * 60)
    print("提取苹果和樱桃子集")
    print("=" * 60)

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    temp_dir = output_path.parent / "temp_plantvillage"
    temp_dir.mkdir(parents=True, exist_ok=True)

    try:
        # 解压
        if archive_path.endswith(('.tar.gz', '.tgz')):
            with tarfile.open(archive_path, 'r:gz') as tar:
                tar.extractall(temp_dir)
        elif archive_path.endswith('.zip'):
            with zipfile.ZipFile(archive_path, 'r') as z:
                z.extractall(temp_dir)
        else:
            print(f"不支持的格式: {archive_path}")
            return False

        # 找到数据目录
        data_dir = temp_dir
        for item in temp_dir.iterdir():
            if item.is_dir():
                subdirs = [d.name for d in item.iterdir() if d.is_dir()]
                if any('Apple' in d or 'Cherry' in d for d in subdirs):
                    data_dir = item
                    break

        # 复制需要的类别
        copied = 0
        for class_name in os.listdir(data_dir):
            if class_name in WANTED_CLASSES:
                src = data_dir / class_name
                dst = output_path / class_name
                dst.mkdir(parents=True, exist_ok=True)
                for img in src.iterdir():
                    if img.suffix.lower() in ('.jpg', '.jpeg', '.png'):
                        shutil.copy2(img, dst / img.name)
                        copied += 1
                print(f"  ✓ {class_name}: {len(list(src.glob('*.jpg')))} 张")

        print(f"\n共复制: {copied} 张图片")
        print(f"输出目录: {output_path}")
        return True

    finally:
        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)


def show_dataset_info(data_dir=None):
    """显示数据集信息"""
    if data_dir is None:
        data_dir = get_plantvillage_dir()

    data_path = Path(data_dir)
    if not data_path.exists():
        print(f"目录不存在: {data_path}")
        return

    print("=" * 60)
    print("PlantVillage 苹果樱桃子集")
    print("=" * 60)

    total = 0
    for class_name in PLANTVILLAGE_CLASSES:
        class_dir = data_path / class_name
        if class_dir.exists():
            count = len(list(class_dir.glob("*.jpg")))
            total += count
            print(f"  {class_name}: {count} 张")
        else:
            print(f"  {class_name}: 缺失")

    print(f"\n总计: {total} 张")
    print("=" * 60)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='PlantVillage 数据集')
    parser.add_argument('--guide', action='store_true', help='显示下载指南')
    parser.add_argument('--extract', type=str, help='提取苹果和樱桃')
    parser.add_argument('--info', action='store_true', help='显示数据集信息')
    args = parser.parse_args()

    if args.guide:
        download_from_kaggle()
    elif args.extract:
        extract_apple_cherry(args.extract)
    elif args.info:
        show_dataset_info()
    else:
        download_from_kaggle()
