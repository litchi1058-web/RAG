# -*- coding: utf-8 -*-
"""
消融实验：Focal Loss
描述：Focal Loss(gamma=2.0)
"""
import subprocess
import sys

def main():
    cmd = [
        'python', 'd:/bf/proj/RAG/lsnet/train.py',
        '--model', 'lsnet',
        '--epochs', '80',
        '--batch-size', '32',
        '--lr', '1e-3',
        '--weight-decay', '1e-4',
        '--patience', '15',
        '--grad-clip', '1.0',
        '--image-size', '224',
        '--use-focal-loss',
        '--focal-gamma', '2.0',
        '--cv-folds', '1',
        '--skip-final-train',
        '--test-freq', '5',
        '--exp-suffix', 'focal_loss'
    ]
    
    print("运行 Focal Loss 实验...")
    print(f"命令: {' '.join(cmd)}")
    
    subprocess.run(cmd, check=True)

if __name__ == '__main__':
    main()