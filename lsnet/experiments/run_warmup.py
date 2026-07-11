# -*- coding: utf-8 -*-
"""
消融实验：学习率预热
描述：LinearWarmup(5 epochs) + CosineAnnealing
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
        '--warmup-epochs', '5',
        '--cv-folds', '1',
        '--skip-final-train',
        '--test-freq', '5',
        '--exp-suffix', 'warmup_5'
    ]
    
    print("运行学习率预热实验...")
    print(f"命令: {' '.join(cmd)}")
    
    subprocess.run(cmd, check=True)

if __name__ == '__main__':
    main()