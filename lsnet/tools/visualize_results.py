# -*- coding: utf-8 -*-
"""
LSNet 训练曲线叠加可视化工具
功能：
  - 多实验训练/验证曲线叠加
  - 按技术家族分组着色
  - 折内曲线差异分析（CV fold 对比）

用法：
  python -m lsnet.tools.visualize_results [--tags mixup,ema] [--top-k 10] [--output-dir path]
"""
import argparse
import sys
from pathlib import Path
from typing import Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from lsnet.tools.experiment_utils import (
    discover_experiments, load_experiment_data,
    get_technique_summary, TECHNIQUE_LABELS,
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


COLOR_CYCLE = [
    '#E74C3C', '#3498DB', '#2ECC71', '#F39C12', '#9B59B6',
    '#1ABC9C', '#E67E22', '#2980B9', '#27AE60', '#C0392B',
    '#16A085', '#8E44AD', '#D35400', '#2C3E50', '#7F8C8D',
]


def collect_experiments_with_history(
    min_folds: int = 0,
    tags: List[str] = None,
    top_k: int = 20,
) -> List[Dict]:
    """收集有 train_history 的实验"""
    exp_dirs = discover_experiments(min_folds=min_folds, tags=tags)
    exp_list = []
    for d in exp_dirs:
        data = load_experiment_data(d)
        if data and data.get('train_history'):
            exp_list.append(data)
    exp_list.sort(key=lambda e: (e.get('cv_data') or {}).get('mean_val_acc', 0), reverse=True)
    return exp_list[:top_k]


def plot_overlay_curves(exp_list: List[Dict], save_dir: Path):
    """叠加绘制多条训练曲线的对比图"""
    if not HAS_MPL:
        print("[WARN] matplotlib 未安装，跳过曲线可视化")
        return
    if not exp_list:
        print("[WARN] 没有找到含训练历史的实验")
        return

    fig, axes = plt.subplots(1, 3, figsize=(18, 6))

    # Loss 叠加
    ax = axes[0]
    for idx, exp in enumerate(exp_list):
        hist = exp['train_history']
        tech = exp['technique_summary'][:20]
        color = COLOR_CYCLE[idx % len(COLOR_CYCLE)]
        train_loss = hist.get('train_loss', [])
        val_loss   = hist.get('val_loss', [])
        if train_loss:
            ax.plot(range(1, len(train_loss) + 1), train_loss, color=color, linestyle='-', alpha=0.8,
                    label=f'{tech} (train)' if idx == 0 else "")
        if val_loss:
            ax.plot(range(1, len(val_loss) + 1), val_loss, color=color, linestyle='--', alpha=0.6)
    ax.set_xlabel('Epoch')
    ax.set_ylabel('Loss')
    ax.set_title('Loss 曲线叠加')
    ax.grid(alpha=0.3)

    # Accuracy 叠加
    ax = axes[1]
    for idx, exp in enumerate(exp_list):
        hist = exp['train_history']
        tech = exp['technique_summary'][:20]
        color = COLOR_CYCLE[idx % len(COLOR_CYCLE)]
        train_acc = hist.get('train_acc', [])
        val_acc   = hist.get('val_acc', [])
        if train_acc:
            ax.plot(range(1, len(train_acc) + 1), train_acc, color=color, linestyle='-', alpha=0.8)
        if val_acc:
            ax.plot(range(1, len(val_acc) + 1), val_acc, color=color, linestyle='--', alpha=0.6,
                    label=tech if idx == 0 else "")
    ax.set_xlabel('Epoch')
    ax.set_ylabel('Accuracy (%)')
    ax.set_title('Accuracy 曲线叠加')
    ax.grid(alpha=0.3)

    if len(exp_list) <= 15:
        short_labels = [e['technique_summary'][:25] for e in exp_list]
        axes[1].legend(short_labels, loc='lower right', fontsize=7)

    # F1 叠加
    ax = axes[2]
    for idx, exp in enumerate(exp_list):
        hist = exp['train_history']
        tech = exp['technique_summary'][:20]
        color = COLOR_CYCLE[idx % len(COLOR_CYCLE)]
        val_f1 = hist.get('val_f1', [])
        if val_f1:
            ax.plot(range(1, len(val_f1) + 1), val_f1, color=color, alpha=0.8, label=tech)
    ax.set_xlabel('Epoch')
    ax.set_ylabel('F1 Score (%)')
    ax.set_title('验证集 F1 曲线叠加')
    ax.grid(alpha=0.3)

    plt.tight_layout()
    save_path = save_dir / "training_curves_overlay.png"
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  曲线叠加图保存: {save_path}")


def plot_best_per_technique(exp_list: List[Dict], save_dir: Path):
    """按技术家族绘制最佳实验的曲线"""
    if not HAS_MPL:
        return

    best_per_tech: Dict[str, Dict] = {}
    for exp in exp_list:
        tags = exp['tags']
        for tech, active in tags.items():
            if not active or tech == 'combo' or tech == 'baseline':
                continue
            cv_data = exp.get('cv_data', {})
            acc = cv_data.get('mean_val_acc', 0) if cv_data else 0
            if tech not in best_per_tech or acc > best_per_tech[tech].get('_score', 0):
                best_per_tech[tech] = {**exp, '_score': acc}

    if len(best_per_tech) < 2:
        return

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    metrics = [('val_acc', '验证 Accuracy (%)'), ('val_f1', '验证 F1 (%)')]

    for ax_idx, (metric_key, ylabel) in enumerate(metrics):
        ax = axes[ax_idx]
        for idx, (tech, exp) in enumerate(best_per_tech.items()):
            hist = exp.get('train_history', {})
            vals = hist.get(metric_key, [])
            if not vals:
                continue
            color = COLOR_CYCLE[idx % len(COLOR_CYCLE)]
            label = TECHNIQUE_LABELS.get(tech, tech)
            ax.plot(range(1, len(vals) + 1), vals, color=color, alpha=0.85,
                    label=label, linewidth=2)
        ax.set_xlabel('Epoch')
        ax.set_ylabel(ylabel)
        ax.set_title(f'{ylabel} — 各技术最佳实验')
        ax.legend(loc='lower right', fontsize=8)
        ax.grid(alpha=0.3)

    plt.tight_layout()
    save_path = save_dir / "best_per_technique.png"
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  各技术最佳曲线保存: {save_path}")


def main():
    parser = argparse.ArgumentParser(description='LSNet 训练曲线可视化工具')
    parser.add_argument('--tags', type=str, default='', help='技术标签过滤')
    parser.add_argument('--top-k', type=int, default=15, help='最多显示实验数')
    parser.add_argument('--output-dir', type=str, default='', help='输出目录')
    args = parser.parse_args()

    tags = [t.strip() for t in args.tags.split(',') if t.strip()] if args.tags else None
    out_dir = Path(args.output_dir) if args.output_dir else Path(__file__).resolve().parent.parent / "results"
    out_dir.mkdir(parents=True, exist_ok=True)

    if HAS_MPL:
        setup_chinese_font()

    exp_list = collect_experiments_with_history(tags=tags, top_k=args.top_k)
    if not exp_list:
        print("[WARN] 没有找到含训练历史的实验")
        return

    print(f"已加载 {len(exp_list)} 个含训练历史的实验")

    plot_overlay_curves(exp_list, out_dir)
    plot_best_per_technique(exp_list, out_dir)

    print(f"\n[完成] 可视化完成 | 输出目录: {out_dir}")


if __name__ == '__main__':
    main()
