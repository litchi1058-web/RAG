# -*- coding: utf-8 -*-
"""
LSNet 实验分析工具集 — 共享模块
功能：实验发现、名称解析、结果加载
"""
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple


RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"
MODELS_DIR  = Path(__file__).resolve().parent.parent / "models"
LOGS_DIR    = Path(__file__).resolve().parent.parent / "logs"


# 技术标签解析规则
# 注意：实验名用 _ 分隔，\b 不识别 _（_ 属于 \w），故用 (?:^|_) / (?=_|$) 替代
_PREFIX = r'(?:^|_)'
_SUFFIX = r'(?=_|$)'

TECHNIQUE_PATTERNS = [
    ('baseline',        rf'{_PREFIX}baseline{_SUFFIX}'),
    ('mixup',           rf'{_PREFIX}mixup{_SUFFIX}'),
    ('ema',             rf'{_PREFIX}ema{_SUFFIX}'),
    ('focal',           rf'{_PREFIX}focal{_SUFFIX}'),
    ('label_smoothing', rf'{_PREFIX}ls{_SUFFIX}'),
    ('warmup',          rf'{_PREFIX}warmup{_SUFFIX}'),
    ('freeze',          rf'{_PREFIX}freeze{_SUFFIX}'),
    ('cbam',            rf'{_PREFIX}cbam{_SUFFIX}'),
    ('distill',         rf'{_PREFIX}distill{_SUFFIX}'),
    ('strong_aug',      rf'{_PREFIX}strong_aug{_SUFFIX}'),
    ('high_res',        rf'{_PREFIX}res\d{3}{_SUFFIX}|{_PREFIX}high_res{_SUFFIX}'),
    ('plantvillage',    rf'{_PREFIX}pv{_SUFFIX}'),
    ('combo',           rf'{_PREFIX}combo{_SUFFIX}'),
]

TECHNIQUE_LABELS = {
    'baseline':        'Baseline',
    'mixup':           'MixUp',
    'ema':             'EMA',
    'focal':           'Focal Loss',
    'label_smoothing': '标签平滑',
    'warmup':          'Warmup',
    'freeze':          'Freeze',
    'cbam':            'CBAM',
    'distill':         '知识蒸馏',
    'strong_aug':      '强增强',
    'high_res':        '高分辨率',
    'plantvillage':    'PlantVillage',
    'combo':           '组合',
}


def discover_experiments(
    results_dir: Optional[Path] = None,
    min_folds: int = 0,
    tags: Optional[List[str]] = None,
    exclude_debug: bool = True,
) -> List[Path]:
    """发现所有实验目录

    Args:
        results_dir: 结果目录（默认 lsnet/results/）
        min_folds: 最少折数过滤（0=不过滤）
        tags: 技术标签过滤（如 ['mixup', 'ema']）
        exclude_debug: 是否排除 debug/test/quick 实验

    Returns:
        实验目录路径列表（按实验名排序）
    """
    results_dir = results_dir or RESULTS_DIR
    if not results_dir.exists():
        return []

    experiments = []
    for d in sorted(results_dir.iterdir()):
        if not d.is_dir():
            continue
        name = d.name

        if exclude_debug and re.search(r'\b(debug|test|quick)\b', name, re.IGNORECASE):
            continue

        cv_file = d / "cv_results.json"
        if not cv_file.exists():
            continue

        if min_folds > 0:
            data = _load_json(cv_file)
            folds = data.get('cv_folds', 0) if data else 0
            if folds < min_folds:
                continue

        if tags:
            exp_tags = parse_experiment_tags(name)
            if not any(t in exp_tags for t in tags):
                continue

        experiments.append(d)

    return experiments


def parse_experiment_tags(exp_name: str) -> Dict[str, bool]:
    """解析实验名中的技术标签"""
    tags = {}
    for key, pattern in TECHNIQUE_PATTERNS:
        tags[key] = bool(re.search(pattern, exp_name, re.IGNORECASE))
    return tags


def get_experiment_short_name(exp_name: str) -> str:
    """从实验名中提取简短名称（去掉模型前缀和时间戳）"""
    name = re.sub(r'_\d{8}_\d{6}$', '', exp_name)
    name = re.sub(r'^lsnet_cv\d+_', '', name)
    return name


def get_technique_summary(exp_name: str) -> str:
    """返回实验所用技术的可读摘要"""
    tags = parse_experiment_tags(exp_name)
    active = [TECHNIQUE_LABELS[k] for k, v in tags.items() if v]
    if not active:
        active = ['无优化']
    if '组合' in active and len(active) > 1:
        active.remove('组合')
    return ' + '.join(active)


def load_experiment_data(exp_dir: Path) -> Optional[Dict]:
    """加载单个实验的全部数据"""
    exp_name = exp_dir.name
    cv_file = exp_dir / "cv_results.json"
    if not cv_file.exists():
        return None

    cv_data = _load_json(cv_file)

    # 查找 train_history：先找 results 目录，再找 models 目录
    train_history = _load_json(exp_dir / "train_history.json")
    if not train_history:
        for sub in exp_dir.iterdir():
            if sub.is_dir() and (sub / "train_history.json").exists():
                train_history = _load_json(sub / "train_history.json")
                if train_history:
                    break
    # 在 models 目录中查找（训练时实际保存位置）
    if not train_history:
        model_dir = MODELS_DIR / exp_dir.name
        if model_dir.exists():
            train_history = _load_json(model_dir / "train_history.json")
            if not train_history:
                for sub in model_dir.iterdir():
                    if sub.is_dir() and (sub / "train_history.json").exists():
                        train_history = _load_json(sub / "train_history.json")
                        if train_history:
                            break
        # 也检查 fold 子目录
        if not train_history:
            for fold_dir in sorted(model_dir.iterdir()):
                if fold_dir.is_dir() and (fold_dir / "train_history.json").exists():
                    train_history = _load_json(fold_dir / "train_history.json")
                    if train_history:
                        break

    return {
        'name': exp_name,
        'dir': exp_dir,
        'tags': parse_experiment_tags(exp_name),
        'short_name': get_experiment_short_name(exp_name),
        'technique_summary': get_technique_summary(exp_name),
        'cv_data': cv_data,
        'train_history': train_history,
        'has_confusion_matrix': any(exp_dir.rglob("confusion_matrix.png")),
        'has_classification_report': any(exp_dir.rglob("classification_report.txt")),
    }


def _load_json(path: Path) -> Optional[Dict]:
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return None


def get_best_result(exp_data: Dict) -> Optional[Dict]:
    """从实验数据中提取最佳结果摘要"""
    cv_data = exp_data.get('cv_data')
    if not cv_data:
        return None
    config = cv_data.get('config', {})

    result = {
        'name': exp_data['name'],
        'short_name': exp_data['short_name'],
        'technique_summary': exp_data['technique_summary'],
        'test_acc': cv_data.get('mean_test_acc', 0),
        'test_f1': cv_data.get('mean_test_f1', 0),
        'val_acc': cv_data.get('mean_val_acc', 0),
        'cv_folds': cv_data.get('cv_folds', 1),
        'lr': config.get('lr', '?'),
        'batch_size': config.get('batch_size', '?'),
        'image_size': config.get('image_size', 224),
        'epochs': config.get('epochs', '?'),
        'weight_decay': config.get('weight_decay', '?'),
        'label_smoothing': config.get('label_smoothing', 0),
        'mixup_alpha': config.get('mixup_alpha', 0),
        'focal_gamma': config.get('focal_gamma', 0),
        'warmup_epochs': config.get('warmup_epochs', 0),
        'use_plantvillage': config.get('use_plantvillage', False),
    }

    cv_results_list = cv_data.get('cv_results', [])
    result['fold_details'] = [
        {'fold': r.get('fold', '?'), 'test_acc': r.get('test_acc', 0),
         'test_f1': r.get('test_f1', 0), 'best_epoch': r.get('best_epoch', '?')}
        for r in cv_results_list
    ]
    return result


def format_table(rows: List[Dict], columns: List[Tuple[str, str, int]], title: str = "") -> str:
    """生成格式化的终端表格"""
    if not rows:
        return "(无数据)"
    header = " | ".join(h.center(w) for _, h, w in columns)
    sep = "-+-".join("-" * w for _, _, w in columns)
    lines = []
    if title:
        total_w = sum(w for _, _, w in columns) + 3 * (len(columns) - 1)
        lines.append(f"\n{'=' * total_w}")
        lines.append(f"  {title}")
        lines.append(f"{'=' * total_w}")
    lines.append(f"| {header} |")
    lines.append(f"| {sep} |")
    for row in rows:
        vals = []
        for key, _, w in columns:
            v = row.get(key, '')
            if isinstance(v, float):
                v = f"{v:.2f}"
            vals.append(str(v).center(w))
        lines.append(f"| {' | '.join(vals)} |")
    return "\n".join(lines)
