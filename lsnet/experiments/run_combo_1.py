# -*- coding: utf-8 -*-
"""
消融实验：组合实验1
描述：MixUp(0.4,0.8) + Label Smoothing(0.1)
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
        '--label-smoothing', '0.1',
        '--cv-folds', '1',
        '--skip-final-train',
        '--test-freq', '5',
        '--exp-suffix', 'combo_mixup_ls'
    ]
    
    print("运行组合实验1...")
    print(f"命令: {' '.join(cmd)}")
    
    subprocess.run(cmd, check=True)

if __name__ == '__main__':
    main()