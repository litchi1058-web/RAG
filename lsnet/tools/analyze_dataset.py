# -*- coding: utf-8 -*-
"""
数据分析工具
"""
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.shared.paths import get_raw_data_dir
from lsnet.data import collect_all_samples, analyze_dataset


def analyze_data(data_dir=None):
    """分析数据集"""
    if data_dir is None:
        data_dir = get_raw_data_dir()

    data_path = Path(data_dir)

    if not data_path.exists():
        print(f"目录不存在: {data_path}")
        return

    print(f"分析目录: {data_path}\n")

    # 汇总所有类别
    all_samples, class_to_idx = collect_all_samples(data_path)

    if not all_samples:
        print("未找到任何样本")
        return

    analyze_dataset(all_samples, class_to_idx, f"数据集 {data_path.name}")

    # 按子目录分别统计
    for sub_dir in data_path.iterdir():
        if sub_dir.is_dir():
            samples, c2i = collect_all_samples(sub_dir)
            if samples:
                analyze_dataset(samples, c2i, sub_dir.name)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='数据分析')
    parser.add_argument('--data-dir', type=str, default=None)
    args = parser.parse_args()

    analyze_data(args.data_dir)
