# -*- coding: utf-8 -*-
"""
LSNet 自动化参数搜索脚本
目标：测试集准确率达到94%以上
"""
import os
import sys
import json
import subprocess
import time
from pathlib import Path
from datetime import datetime

# 项目路径
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# 参数搜索空间
PARAM_GRID = {
    # 学习率
    'lr': [1e-3, 5e-4, 2e-4, 1e-4],
    
    # MixUp参数
    'mixup_alpha': [0.2, 0.4, 0.6, 0.8],
    'mixup_prob': [0.5, 0.7, 0.8, 1.0],
    
    # Label Smoothing
    'label_smoothing': [0.0, 0.05, 0.1, 0.15],
    
    # 训练参数
    'epochs': [100, 150, 200],
    'batch_size': [16, 32, 64],
    'weight_decay': [1e-4, 5e-5, 1e-5],
    
    # 其他技术
    'use_ema': [True, False],
    'freeze_epochs': [0, 3, 5],
    'warmup_epochs': [0, 3, 5],
    'use_focal_loss': [True, False],
    'focal_gamma': [2.0, 3.0],
    
    # 图像尺寸
    'image_size': [224, 256, 288],
    
    # 早停
    'patience': [15, 20, 25, 30],
}

# 基于之前实验的最佳配置，设计优先测试的组合
PRIORITY_CONFIGS = [
    # 配置1: MixUp + Label Smoothing (之前最佳组合的优化)
    {
        'name': 'mixup_ls_optimized',
        'lr': 5e-4,
        'epochs': 150,
        'batch_size': 32,
        'mixup_alpha': 0.4,
        'mixup_prob': 0.8,
        'label_smoothing': 0.05,
        'use_ema': True,
        'freeze_epochs': 3,
        'warmup_epochs': 3,
        'patience': 25,
        'image_size': 224,
    },
    
    # 配置2: 强MixUp + EMA
    {
        'name': 'strong_mixup_ema',
        'lr': 1e-3,
        'epochs': 200,
        'batch_size': 32,
        'mixup_alpha': 0.6,
        'mixup_prob': 1.0,
        'label_smoothing': 0.0,
        'use_ema': True,
        'freeze_epochs': 0,
        'warmup_epochs': 5,
        'patience': 30,
        'image_size': 224,
    },
    
    # 配置3: Focal Loss + MixUp
    {
        'name': 'focal_mixup',
        'lr': 5e-4,
        'epochs': 150,
        'batch_size': 32,
        'mixup_alpha': 0.4,
        'mixup_prob': 0.8,
        'label_smoothing': 0.0,
        'use_ema': False,
        'freeze_epochs': 0,
        'warmup_epochs': 0,
        'use_focal_loss': True,
        'focal_gamma': 2.0,
        'patience': 20,
        'image_size': 224,
    },
    
    # 配置4: 全技术组合优化版
    {
        'name': 'full_combo_optimized',
        'lr': 5e-4,
        'epochs': 150,
        'batch_size': 32,
        'mixup_alpha': 0.4,
        'mixup_prob': 0.7,
        'label_smoothing': 0.05,
        'use_ema': True,
        'freeze_epochs': 3,
        'warmup_epochs': 3,
        'use_focal_loss': True,
        'focal_gamma': 2.0,
        'patience': 25,
        'image_size': 224,
    },
    
    # 配置5: 大batch + MixUp
    {
        'name': 'large_batch_mixup',
        'lr': 1e-3,
        'epochs': 100,
        'batch_size': 64,
        'mixup_alpha': 0.4,
        'mixup_prob': 0.8,
        'label_smoothing': 0.1,
        'use_ema': True,
        'freeze_epochs': 0,
        'warmup_epochs': 0,
        'patience': 20,
        'image_size': 224,
    },
    
    # 配置6: 高分辨率 + MixUp
    {
        'name': 'high_res_mixup',
        'lr': 5e-4,
        'epochs': 150,
        'batch_size': 16,
        'mixup_alpha': 0.4,
        'mixup_prob': 0.8,
        'label_smoothing': 0.05,
        'use_ema': True,
        'freeze_epochs': 3,
        'warmup_epochs': 3,
        'patience': 25,
        'image_size': 288,
    },
    
    # 配置7: 小学习率长训练
    {
        'name': 'low_lr_long_train',
        'lr': 2e-4,
        'epochs': 200,
        'batch_size': 32,
        'mixup_alpha': 0.4,
        'mixup_prob': 0.8,
        'label_smoothing': 0.05,
        'use_ema': True,
        'freeze_epochs': 5,
        'warmup_epochs': 5,
        'patience': 30,
        'image_size': 224,
    },
    
    # 配置8: 极强MixUp
    {
        'name': 'extreme_mixup',
        'lr': 1e-3,
        'epochs': 200,
        'batch_size': 32,
        'mixup_alpha': 0.8,
        'mixup_prob': 1.0,
        'label_smoothing': 0.0,
        'use_ema': True,
        'freeze_epochs': 0,
        'warmup_epochs': 0,
        'patience': 30,
        'image_size': 224,
    },
]


def build_command(config):
    """
    根据配置构建训练命令
    
    Args:
        config: dict 参数配置
        
    Returns:
        list: 命令参数列表
    """
    cmd = [
        'python',
        str(PROJECT_ROOT / 'lsnet' / 'train.py'),
        '--model', 'lsnet',
        '--epochs', str(config['epochs']),
        '--batch-size', str(config['batch_size']),
        '--lr', str(config['lr']),
        '--weight-decay', str(config.get('weight_decay', 1e-4)),
        '--patience', str(config['patience']),
        '--grad-clip', '1.0',
        '--image-size', str(config['image_size']),
        '--cv-folds', '1',
        '--skip-final-train',
        '--test-freq', '5',
        '--exp-suffix', config['name'],
    ]
    
    # MixUp
    if config.get('mixup_alpha', 0) > 0:
        cmd.extend([
            '--use-mixup',
            '--mixup-alpha', str(config['mixup_alpha']),
            '--mixup-prob', str(config['mixup_prob']),
        ])
    
    # Label Smoothing
    if config.get('label_smoothing', 0) > 0:
        cmd.extend(['--label-smoothing', str(config['label_smoothing'])])
    
    # EMA
    if config.get('use_ema', False):
        cmd.extend(['--use-ema'])
    
    # Freeze
    if config.get('freeze_epochs', 0) > 0:
        cmd.extend(['--freeze-epochs', str(config['freeze_epochs'])])
    
    # Warmup
    if config.get('warmup_epochs', 0) > 0:
        cmd.extend(['--warmup-epochs', str(config['warmup_epochs'])])
    
    # Focal Loss
    if config.get('use_focal_loss', False):
        cmd.extend([
            '--use-focal-loss',
            '--focal-gamma', str(config.get('focal_gamma', 2.0)),
        ])
    
    return cmd


def run_experiment(config, results_log):
    """
    运行单个实验
    
    Args:
        config: dict 参数配置
        results_log: list 结果日志
        
    Returns:
        dict: 实验结果
    """
    print(f"\n{'='*70}")
    print(f"实验: {config['name']}")
    print(f"{'='*70}")
    print(f"配置:")
    for key, value in config.items():
        if key != 'name':
            print(f"  {key}: {value}")
    print()
    
    # 构建命令
    cmd = build_command(config)
    
    # 记录开始时间
    start_time = time.time()
    
    # 运行训练
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=3600 * 2  # 2小时超时
        )
        
        # 解析结果
        output = result.stdout
        
        # 查找测试结果
        test_acc = None
        test_f1 = None
        
        for line in output.split('\n'):
            if '测试结果:' in line or 'Test:' in line:
                # 解析准确率
                parts = line.split(',')
                for part in parts:
                    if 'acc=' in part:
                        try:
                            acc_str = part.split('acc=')[1].split('%')[0]
                            test_acc = float(acc_str)
                        except:
                            pass
                    if 'f1=' in part:
                        try:
                            f1_str = part.split('f1=')[1].split('%')[0]
                            test_f1 = float(f1_str)
                        except:
                            pass
        
        elapsed_time = time.time() - start_time
        
        experiment_result = {
            'name': config['name'],
            'config': config,
            'test_acc': test_acc,
            'test_f1': test_f1,
            'elapsed_time': elapsed_time,
            'success': result.returncode == 0,
            'output': output[-2000:] if len(output) > 2000 else output,
        }
        
        # 打印结果
        if test_acc:
            print(f"\n结果:")
            print(f"  测试准确率: {test_acc:.2f}%")
            print(f"  测试F1: {test_f1:.2f}%")
            print(f"  训练时间: {elapsed_time:.1f}秒")
            
            if test_acc >= 94.0:
                print(f"\n  ★★★ 达到目标！准确率 >= 94% ★★★")
        else:
            print(f"\n未能解析测试结果")
        
        results_log.append(experiment_result)
        
        return experiment_result
        
    except subprocess.TimeoutExpired:
        print(f"\n实验超时（超过2小时）")
        return {
            'name': config['name'],
            'config': config,
            'test_acc': None,
            'test_f1': None,
            'success': False,
            'error': 'timeout',
        }
    except Exception as e:
        print(f"\n实验失败: {e}")
        return {
            'name': config['name'],
            'config': config,
            'test_acc': None,
            'test_f1': None,
            'success': False,
            'error': str(e),
        }


def main():
    """主函数"""
    print("=" * 70)
    print("LSNet 自动化参数搜索")
    print("目标: 测试集准确率 >= 94%")
    print("=" * 70)
    
    # 结果日志
    results_log = []
    
    # 开始时间
    total_start = time.time()
    
    # 运行优先配置
    print(f"\n将测试 {len(PRIORITY_CONFIGS)} 个优先配置...")
    
    best_result = None
    successful_configs = []
    
    for i, config in enumerate(PRIORITY_CONFIGS, 1):
        print(f"\n[{i}/{len(PRIORITY_CONFIGS)}] 测试配置: {config['name']}")
        
        result = run_experiment(config, results_log)
        
        if result['success'] and result['test_acc']:
            successful_configs.append(result)
            
            # 检查是否达到目标
            if result['test_acc'] >= 94.0:
                best_result = result
                print(f"\n{'='*70}")
                print(f"找到达到目标的配置！")
                print(f"{'='*70}")
                break
    
    # 总时间
    total_elapsed = time.time() - total_start
    
    # 打印汇总
    print(f"\n{'='*70}")
    print(f"参数搜索完成")
    print(f"{'='*70}")
    print(f"\n总耗时: {total_elapsed:.1f}秒 ({total_elapsed/60:.1f}分钟)")
    print(f"成功实验: {len(successful_configs)}/{len(PRIORITY_CONFIGS)}")
    
    # 按准确率排序
    if successful_configs:
        successful_configs.sort(key=lambda x: x['test_acc'], reverse=True)
        
        print(f"\n结果排名:")
        print(f"{'排名':<4} {'配置名称':<25} {'准确率':<10} {'F1':<10} {'时间':<10}")
        print("-" * 60)
        
        for i, r in enumerate(successful_configs, 1):
            time_str = f"{r['elapsed_time']:.0f}s"
            print(f"{i:<4} {r['name']:<25} {r['test_acc']:.2f}%{'':<5} {r['test_f1']:.2f}%{'':<5} {time_str:<10}")
        
        # 最佳配置
        best = successful_configs[0]
        print(f"\n最佳配置:")
        print(f"  名称: {best['name']}")
        print(f"  准确率: {best['test_acc']:.2f}%")
        print(f"  F1: {best['test_f1']:.2f}%")
        
        if best['test_acc'] >= 94.0:
            print(f"\n  ★★★ 目标达成！ ★★★")
        else:
            gap = 94.0 - best['test_acc']
            print(f"\n  距离目标还差: {gap:.2f}%")
            print(f"\n建议:")
            print(f"  1. 尝试更长的训练时间 (epochs=250+)")
            print(f"  2. 尝试更强的数据增强")
            print(f"  3. 尝试更大的模型")
            print(f"  4. 收集更多训练数据")
    
    # 保存结果
    results_file = PROJECT_ROOT / 'lsnet' / 'results' / 'auto_search_results.json'
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'total_elapsed': total_elapsed,
            'target_accuracy': 94.0,
            'results': results_log,
            'best_config': successful_configs[0] if successful_configs else None,
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n结果已保存至: {results_file}")
    
    return best_result


if __name__ == '__main__':
    main()