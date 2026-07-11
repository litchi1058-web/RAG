# -*- coding: utf-8 -*-
"""
LSNet 实验对比分析工具
功能：
  - 聚合所有实验结果 → 排名表
  - 按技术家族分组对比
  - 生成对比柱状图
  - 超参 vs 性能相关性分析
  - 导出 CSV 对比表

用法：
  python -m lsnet.tools.compare_experiments [--min-folds N] [--tags mixup,ema] [--top-k N] [--export-csv path]
"""
import argparse
import csv
import sys
from pathlib import Path
from typing import Dict, List

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from lsnet.tools.experiment_utils import (
    discover_experiments, load_experiment_data, get_best_result,
    format_table, TECHNIQUE_LABELS,
)
from lsnet.tools._plot_config import setup_chinese_font, force_utf8_output

force_utf8_output()

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    HAS_MPL = True
except ImportError:
    HAS_MPL = False


def collect_results(min_folds: int = 0, tags: List[str] = None) -> List[Dict]:
    """收集并排序所有实验结果"""
    exp_dirs = discover_experiments(min_folds=min_folds, tags=tags)
    results = []
    for d in exp_dirs:
        data = load_experiment_data(d)
        if data:
            best = get_best_result(data)
            if best:
                results.append(best)
    results.sort(key=lambda r: r['test_acc'], reverse=True)
    return results


def print_ranking(results: List[Dict]):
    """打印排名表"""
    columns = [
        ('rank',       '#',   4),
        ('short_name', '实验', 40),
        ('test_acc',   '测试Acc', 10),
        ('test_f1',    '测试F1', 10),
        ('val_acc',    '验证Acc', 10),
        ('cv_folds',   '折数',  6),
        ('technique_summary', '技术', 35),
    ]
    rows = []
    for i, r in enumerate(results, 1):
        rows.append({
            'rank': str(i),
            'short_name': r['short_name'][:38],
            'test_acc': r['test_acc'],
            'test_f1': r['test_f1'],
            'val_acc': r['val_acc'],
            'cv_folds': r['cv_folds'],
            'technique_summary': r['technique_summary'],
        })
    print(format_table(rows, columns, title=f"实验排名（共 {len(results)} 个实验）"))


def print_hyperparams(results: List[Dict]):
    """打印超参详情表"""
    columns = [
        ('rank',       '#',   4),
        ('short_name', '实验', 32),
        ('test_acc',   'Acc',  7),
        ('lr',         'LR',   10),
        ('batch_size', 'Batch', 7),
        ('image_size', 'Res',  5),
        ('label_smoothing', 'LS', 5),
        ('mixup_alpha', 'MixUpα', 7),
        ('focal_gamma', 'Focalγ', 7),
        ('warmup_epochs', 'Warmup', 7),
    ]
    rows = []
    for i, r in enumerate(results, 1):
        rows.append({
            'rank': str(i),
            'short_name': r['short_name'][:30],
            'test_acc': r['test_acc'],
            'lr': r['lr'],
            'batch_size': r['batch_size'],
            'image_size': r['image_size'],
            'label_smoothing': r['label_smoothing'],
            'mixup_alpha': r['mixup_alpha'],
            'focal_gamma': r['focal_gamma'],
            'warmup_epochs': r['warmup_epochs'],
        })
    print(format_table(rows, columns, title="超参详情表"))


def print_technique_summary(results: List[Dict]):
    """按技术家族分组统计平均性能"""
    technique_results: Dict[str, List[float]] = {}

    for r in results:
        from lsnet.tools.experiment_utils import parse_experiment_tags
        exp_tags = parse_experiment_tags(r['name'])
        active = [k for k, v in exp_tags.items() if v]
        if not active:
            active = ['baseline']
        for tech in active:
            if tech not in technique_results:
                technique_results[tech] = []
            technique_results[tech].append(r['test_acc'])

    if not technique_results:
        return

    sorted_techs = sorted(technique_results.items(), key=lambda x: np.mean(x[1]), reverse=True)
    columns = [
        ('tech',     '技术',   20),
        ('count',    '实验数',  8),
        ('mean_acc', '平均Acc', 10),
        ('std_acc',  'Std',    8),
        ('max_acc',  '最佳Acc', 10),
    ]
    rows = []
    for tech, accs in sorted_techs:
        rows.append({
            'tech': TECHNIQUE_LABELS.get(tech, tech),
            'count': len(accs),
            'mean_acc': np.mean(accs),
            'std_acc': np.std(accs),
            'max_acc': np.max(accs),
        })
    print(format_table(rows, columns, title="按技术家族分组统计"))


def plot_ranking_chart(results: List[Dict], save_path: Path):
    """生成排名柱状图"""
    if not HAS_MPL:
        print("[WARN] matplotlib 未安装，跳过图表生成")
        return

    top_n = min(20, len(results))
    names = [r['short_name'][:25] for r in results[:top_n]]
    accs  = [r['test_acc'] for r in results[:top_n]]
    f1s   = [r['test_f1'] for r in results[:top_n]]

    fig, ax = plt.subplots(figsize=(14, max(6, top_n * 0.4)))
    y_pos = range(len(names))

    bars_acc = ax.barh([x + 0.2 for x in y_pos], accs, height=0.35, label='Test Acc (%)', color='#4CAF50')
    bars_f1  = ax.barh([x - 0.2 for x in y_pos], f1s,  height=0.35, label='Test F1 (%)', color='#2196F3')

    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names, fontsize=9)
    ax.set_xlabel('Score (%)')
    ax.set_title(f'LSNet 实验排名（Top-{top_n}）')
    ax.legend(loc='lower right')
    ax.grid(axis='x', alpha=0.3)

    for bar in bars_acc:
        w = bar.get_width()
        ax.text(w + 0.3, bar.get_y() + bar.get_height() / 2, f'{w:.1f}',
                va='center', fontsize=8, color='green')
    for bar in bars_f1:
        w = bar.get_width()
        ax.text(w + 0.3, bar.get_y() + bar.get_height() / 2, f'{w:.1f}',
                va='center', fontsize=8, color='blue')

    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  排名图保存: {save_path}")


def plot_technique_comparison(results: List[Dict], save_path: Path):
    """按技术家族生成对比箱线图"""
    if not HAS_MPL:
        return

    from lsnet.tools.experiment_utils import parse_experiment_tags

    tech_data: Dict[str, List[float]] = {}
    for r in results:
        exp_tags = parse_experiment_tags(r['name'])
        active = [k for k, v in exp_tags.items() if v]
        if not active:
            active = ['baseline']
        for tech in active:
            if tech not in tech_data:
                tech_data[tech] = []
            tech_data[tech].append(r['test_acc'])

    if len(tech_data) < 2:
        return

    sorted_techs = sorted(tech_data.items(), key=lambda x: np.mean(x[1]), reverse=True)
    labels = [TECHNIQUE_LABELS.get(t, t) for t, _ in sorted_techs]
    data   = [d for _, d in sorted_techs]

    fig, ax = plt.subplots(figsize=(10, 5))
    bp = ax.boxplot(data, labels=labels, patch_artist=True, showmeans=True,
                    meanprops=dict(marker='D', markerfacecolor='red', markersize=6))

    colors = plt.cm.Set3([i / len(data) for i in range(len(data))])
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)

    ax.set_ylabel('Test Accuracy (%)')
    ax.set_title('各技术家族对比（箱线图）')
    ax.tick_params(axis='x', rotation=30)
    ax.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  技术对比图保存: {save_path}")


def export_csv(results: List[Dict], save_path: Path):
    """导出 CSV 对比表"""
    fields = ['rank', 'short_name', 'test_acc', 'test_f1', 'val_acc',
              'cv_folds', 'lr', 'batch_size', 'image_size',
              'label_smoothing', 'mixup_alpha', 'focal_gamma', 'warmup_epochs',
              'technique_summary']
    with open(save_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        for i, r in enumerate(results, 1):
            r['rank'] = i
            writer.writerow(r)
    print(f"  CSV 导出: {save_path}")


def main():
    parser = argparse.ArgumentParser(description='LSNet 实验对比分析工具')
    parser.add_argument('--min-folds', type=int, default=0, help='最少折数过滤')
    parser.add_argument('--tags', type=str, default='', help='技术标签过滤（逗号分隔）')
    parser.add_argument('--top-k', type=int, default=0, help='只显示 Top-K')
    parser.add_argument('--export-csv', type=str, default='', help='导出 CSV 路径')
    parser.add_argument('--output-dir', type=str, default='', help='图表输出目录')
    args = parser.parse_args()

    tags = [t.strip() for t in args.tags.split(',') if t.strip()] if args.tags else None

    if HAS_MPL:
        setup_chinese_font()

    results = collect_results(min_folds=args.min_folds, tags=tags)

    if not results:
        print("未找到实验数据")
        return

    if args.top_k > 0:
        results = results[:args.top_k]

    print_ranking(results)
    print_hyperparams(results)
    print_technique_summary(results)

    if args.export_csv:
        export_csv(results, Path(args.export_csv))

    out_dir = Path(args.output_dir) if args.output_dir else Path(__file__).resolve().parent.parent / "results"
    out_dir.mkdir(parents=True, exist_ok=True)

    plot_ranking_chart(results, out_dir / "experiment_ranking.png")
    plot_technique_comparison(results, out_dir / "technique_comparison.png")

    print(f"\n[完成] 分析完成 | 共 {len(results)} 个实验")


if __name__ == '__main__':
    main()
