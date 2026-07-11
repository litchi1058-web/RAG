# -*- coding: utf-8 -*-
"""
消融实验：高分辨率
描述：图像尺寸=384
"""
import subprocess
import sys

def main():
    cmd = [
        'python', 'd:/bf/proj/RAG/lsnet/train.py',
        '--model', 'lsnet',
        '--epochs', '80',
        '--batch-size', '16',
        '--lr', '1e-3',
        '--weight-decay', '1e-4',
        '--patience', '15',
        '--grad-clip', '1.0',
        '--image-size', '384',
        '--cv-folds', '1',
        '--skip-final-train',
        '--test-freq', '5',
        '--exp-suffix', 'high_res_384'
    ]
    
    print("运行高分辨率实验...")
    print(f"命令: {' '.join(cmd)}")
    
    subprocess.run(cmd, check=True)

if __name__ == '__main__':
    main()