# -*- coding: utf-8 -*-
"""
消融实验：组合实验2
描述：MixUp + Warmup(5) + EMA
"""
import subprocess
import sys

def main():
    cmd = [
        'python', 'd:/bf/proj/RAG/lsnet/train.py',
        '--model', 'lsnet',
        '--epochs', '100',
        '--batch-size', '32',
        '--lr', '1e-3',
        '--weight-decay', '1e-4',
        '--patience', '20',
        '--grad-clip', '1.0',
        '--image-size', '224',
        '--use-mixup',
        '--mixup-alpha', '0.4',
        '--mixup-prob', '0.8',
        '--warmup-epochs', '5',
        '--use-ema',
        '--cv-folds', '1',
        '--skip-final-train',
        '--test-freq', '5',
        '--exp-suffix', 'combo_mixup_warmup_ema'
    ]
    
    print("运行组合实验2...")
    print(f"命令: {' '.join(cmd)}")
    
    subprocess.run(cmd, check=True)

if __name__ == '__main__':
    main()