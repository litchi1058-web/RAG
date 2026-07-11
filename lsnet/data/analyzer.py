# -*- coding: utf-8 -*-
"""
数据集分析工具
"""
import os
from pathlib import Path
from PIL import Image
from collections import Counter


def analyze_dataset(samples, class_to_idx, dataset_name="数据集", logger=None):
    """分析数据集分布并返回统计信息"""
    idx_to_class = {i: cls for cls, i in class_to_idx.items()}
    class_counts = [0] * len(class_to_idx)
    resolutions = []
    total_size = 0

    for img_path, label in samples:
        class_counts[label] += 1
        try:
            with Image.open(img_path) as img:
                resolutions.append(img.size)
                total_size += os.path.getsize(img_path)
        except:
            resolutions.append((0, 0))

    def _out(msg):
        if logger:
            logger(msg, also_print=True)
        else:
            print(msg)

    _out(f"\n{'='*60}")
    _out(f"{dataset_name} 统计信息")
    _out(f"{'='*60}")
    _out(f"总样本数: {len(samples)}")
    _out(f"类别数: {len(class_to_idx)}")
    _out(f"类别分布:")
    for cls, idx in class_to_idx.items():
        _out(f"  {cls}: {class_counts[idx]} 张 ({class_counts[idx]/len(samples)*100:.2f}%)")

    # 分辨率统计
    unique_resolutions = {}
    for w, h in resolutions:
        key = f"{w}x{h}"
        unique_resolutions[key] = unique_resolutions.get(key, 0) + 1

    _out(f"\n分辨率分布 (前10种):")
    sorted_resolutions = sorted(unique_resolutions.items(), key=lambda x: -x[1])[:10]
    for res, cnt in sorted_resolutions:
        _out(f"  {res}: {cnt} 张")

    if resolutions:
        avg_width = sum(r[0] for r in resolutions) / len(resolutions)
        avg_height = sum(r[1] for r in resolutions) / len(resolutions)
        _out(f"平均分辨率: {avg_width:.0f} x {avg_height:.0f}")
    _out(f"总文件大小: {total_size / (1024*1024):.2f} MB")
    _out(f"{'='*60}\n")

    return {
        'total_samples': len(samples),
        'num_classes': len(class_to_idx),
        'class_counts': class_counts,
        'class_names': list(class_to_idx.keys()),
        'avg_resolution': (avg_width, avg_height) if resolutions else (0, 0),
        'resolution_distribution': dict(sorted_resolutions),
        'total_size_mb': total_size / (1024*1024)
    }
