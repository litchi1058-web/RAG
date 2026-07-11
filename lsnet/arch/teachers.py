# -*- coding: utf-8 -*-
"""
LSNet 教师模型模块

提供基于 VGG19 的教师模型，集成 CBAM 和 SE 注意力机制。
"""

import torch
import torch.nn as nn

from .attention import CBAM, SEBlock


class VGG19CBAM(nn.Module):
    def __init__(self, num_classes: int = 9, pretrained: bool = True, use_cbam: bool = True, use_se: bool = True):
        super().__init__()
        from torchvision.models import vgg19, VGG19_Weights
        base = vgg19(weights=VGG19_Weights.IMAGENET1K_V1 if pretrained else None)
        self.features = base.features
        self.use_cbam = use_cbam; self.use_se = use_se
        if use_cbam: self.cbam3 = CBAM(256); self.cbam4 = CBAM(512); self.cbam5 = CBAM(512)
        if use_se: self.se4 = SEBlock(512)
        self.avgpool = nn.AdaptiveAvgPool2d((1,1))
        self.classifier = nn.Sequential(nn.Linear(512, 1024), nn.BatchNorm1d(1024), nn.ReLU(inplace=True), nn.Dropout(0.4),
                                        nn.Linear(1024, 512), nn.BatchNorm1d(512), nn.ReLU(inplace=True), nn.Dropout(0.3), nn.Linear(512, num_classes))
    def forward(self, x):
        for idx, layer in enumerate(self.features):
            x = layer(x)
            if self.use_cbam:
                if idx == 16: x = self.cbam3(x)
                if idx == 23: x = self.cbam4(x)
                if idx == 30: x = self.cbam5(x)
            if self.use_se and idx == 23: x = self.se4(x)
        x = self.avgpool(x); x = torch.flatten(x, 1); return self.classifier(x)
