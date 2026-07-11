"""简单测试教师模型加载"""
import torch
from pathlib import Path

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"设备: {device}")

# 尝试加载教师模型
teacher_path = "d:\\bf\\proj\\RAG\\vgg-data\\xiaorong_shiyan\\results\\Full\\best_model.pth"
print(f"\n加载教师模型: {teacher_path}")

try:
    checkpoint = torch.load(teacher_path, map_location=device, weights_only=False)
    print(f"✓ 成功加载")
    print(f"Checkpoint keys: {list(checkpoint.keys())}")
    
    if 'model_state_dict' in checkpoint:
        print(f"  model_state_dict keys (前5个): {list(checkpoint['model_state_dict'].keys())[:5]}")
    elif 'state_dict' in checkpoint:
        print(f"  state_dict keys (前5个): {list(checkpoint['state_dict'].keys())[:5]}")
    else:
        print(f"  keys (前5个): {list(checkpoint.keys())[:5]}")
        
except Exception as e:
    print(f"✗ 加载失败: {e}")
    import traceback
    traceback.print_exc()