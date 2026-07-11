# -*- coding: utf-8 -*-
"""
模型构建器
支持多种模型架构 + 加载 LSNet 预训练权重
"""
import torch
import torch.nn as nn
import torchvision.models as tv_models
from pathlib import Path
from .lsnet import LSNet

# LSNet 预训练权重路径
LSNET_PRETRAINED_PATH = Path(__file__).resolve().parent.parent / "models" / "lsnet_t.pth"


def _load_lsnet_pretrained(model, num_classes, verbose=True):
    """
    加载 lsnet/models/lsnet_t.pth 预训练权重（ImageNet-1K, 1000 类）.
    支持动态分辨率的 Attention 模块
    """
    if not LSNET_PRETRAINED_PATH.exists():
        if verbose:
            print(f"[LSNet] 预训练权重不存在: {LSNET_PRETRAINED_PATH}，随机初始化")
        return model

    try:
        raw = torch.load(LSNET_PRETRAINED_PATH, map_location='cpu', weights_only=False)
        pt_sd = raw['model'] if isinstance(raw, dict) and 'model' in raw else raw

        our_sd = model.state_dict()
        # 过滤分类头（输出维度不同）
        head_keys = {'head.bn.weight', 'head.bn.bias', 'head.bn.running_mean',
                     'head.bn.running_var', 'head.bn.num_batches_tracked',
                     'head.l.weight', 'head.l.bias'}

        loaded = {}
        for k in our_sd:
            if k in head_keys:
                continue
            if k not in pt_sd:
                continue
            
            # 处理 attention_biases 的维度不匹配（支持动态分辨率）
            if 'attention_biases' in k:
                pt_shape = pt_sd[k].shape
                our_shape = our_sd[k].shape
                if pt_shape[0] == our_shape[0]:  # num_heads 相同
                    # 截取或填充 attention_biases
                    min_size = min(pt_shape[1], our_shape[1])
                    if min_size > 0:
                        loaded[k] = pt_sd[k][:, :min_size]
                        # 如果目标更大，填充剩余部分
                        if our_shape[1] > min_size:
                            padding = torch.zeros(our_shape[0], our_shape[1] - min_size)
                            loaded[k] = torch.cat([loaded[k], padding], dim=1)
                continue
            
            if pt_sd[k].shape == our_sd[k].shape:
                loaded[k] = pt_sd[k]

        if loaded:
            our_sd.update(loaded)
            model.load_state_dict(our_sd, strict=False)

        if verbose:
            total = len(our_sd)
            loaded_cnt = len(loaded)
            loaded_params = sum(v.numel() for v in loaded.values())
            total_params = sum(v.numel() for v in our_sd.values())
            print(f"[LSNet] 预训练加载: {loaded_cnt}/{total} 层 "
                  f"({loaded_params/1e6:.2f}M / {total_params/1e6:.2f}M 参数, "
                  f"{loaded_params/total_params*100:.1f}%)")

    except Exception as e:
        if verbose:
            print(f"[LSNet] 预训练加载失败: {e}，随机初始化")

    return model


def build_model(model_name='lsnet', num_classes=9, pretrained=True, **kwargs):
    """
    构建模型
    Args:
        model_name: 模型名称
        num_classes: 类别数
        pretrained: 是否加载预训练权重
    """
    model_name = model_name.lower()

    if model_name == 'lsnet':
        model = LSNet(
            num_classes=num_classes,
        )
        if pretrained:
            model = _load_lsnet_pretrained(model, num_classes,
                                           verbose=kwargs.get('verbose', True))

    elif model_name == 'mobilenetv2':
        weights = tv_models.MobileNet_V2_Weights.IMAGENET1K_V1 if pretrained else None
        model = tv_models.mobilenet_v2(weights=weights)
        model.classifier[1] = nn.Linear(model.last_channel, num_classes)

    elif model_name == 'mobilenetv3':
        weights = tv_models.MobileNet_V3_Small_Weights.IMAGENET1K_V1 if pretrained else None
        model = tv_models.mobilenet_v3_small(weights=weights)
        model.classifier[3] = nn.Linear(model.classifier[3].in_features, num_classes)

    elif model_name == 'efficientnetb0':
        weights = tv_models.EfficientNet_B0_Weights.IMAGENET1K_V1 if pretrained else None
        model = tv_models.efficientnet_b0(weights=weights)
        model.classifier[1] = nn.Linear(model.classifier[1].in_features, num_classes)

    elif model_name == 'shufflenetv2':
        weights = tv_models.ShuffleNet_V2_X1_0_Weights.IMAGENET1K_V1 if pretrained else None
        model = tv_models.shufflenet_v2_x1_0(weights=weights)
        model.fc = nn.Linear(model.fc.in_features, num_classes)

    elif model_name == 'resnet18':
        weights = tv_models.ResNet18_Weights.IMAGENET1K_V1 if pretrained else None
        model = tv_models.resnet18(weights=weights)
        model.fc = nn.Linear(model.fc.in_features, num_classes)

    else:
        raise ValueError(f"不支持的模型: {model_name}")

    return model
