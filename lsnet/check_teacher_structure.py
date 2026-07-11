"""查看教师模型结构"""
import torch

teacher_path = "d:\\bf\\proj\\RAG\\vgg-data\\xiaorong_shiyan\\results\\Full\\best_model.pth"
checkpoint = torch.load(teacher_path, map_location='cpu', weights_only=False)

print("Checkpoint keys:", checkpoint.keys())
print("\nmodel_state_dict keys:")
for key in sorted(checkpoint['model_state_dict'].keys()):
    print(f"  {key}: {checkpoint['model_state_dict'][key].shape}")