# -*- coding: utf-8 -*-
"""
消融实验：MixUp/CutMix
描述：MixUp(alpha=0.4, prob=0.8)
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
        '--cv-folds', '1',
        '--skip-final-train',
        '--test-freq', '5',
        '--exp-suffix', 'mixup_0.4'
    ]
    
    print("运行 MixUp 实验...")
    print(f"命令: {' '.join(cmd)}")
    
    subprocess.run(cmd, check=True)

if __name__ == '__main__':
    main()