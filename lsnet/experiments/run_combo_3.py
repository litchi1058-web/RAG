# -*- coding: utf-8 -*-
"""
消融实验：组合实验3
描述：MixUp + Label Smoothing + Warmup + EMA + Freeze(3)
"""
import subprocess
import sys

def main():
    cmd = [
        'python', 'd:/bf/proj/RAG/lsnet/train.py',
        '--model', 'lsnet',
        '--use-cbam',
        '--epochs', '120',
        '--batch-size', '32',
        '--lr', '5e-4',
        '--weight-decay', '1e-4',
        '--patience', '25',
        '--grad-clip', '1.0',
        '--image-size', '224',
        '--use-mixup',
        '--mixup-alpha', '0.4',
        '--mixup-prob', '0.8',
        '--label-smoothing', '0.1',
        '--warmup-epochs', '5',
        '--freeze-epochs', '3',
        '--use-ema',
        '--cv-folds', '1',
        '--skip-final-train',
        '--test-freq', '5',
        '--exp-suffix', 'combo_full'
    ]
    
    print("运行组合实验3 (全量增强)...")
    print(f"命令: {' '.join(cmd)}")
    
    subprocess.run(cmd, check=True)

if __name__ == '__main__':
    main()