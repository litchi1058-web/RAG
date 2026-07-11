# -*- coding: utf-8 -*-
"""
LSNet 注意力机制模块

提供 CBAM（卷积块注意力模块）和 SEBlock（压缩激励模块）实现。
"""

import torch
import torch.nn as nn


class CBAM(nn.Module):
    def __init__(self, channels: int, reduction: int = 16):
        super().__init__()
        mid = max(4, channels // reduction)
        self.mlp = nn.Sequential(nn.Conv2d(channels, mid, kernel_size=1, bias=False), nn.ReLU(inplace=True), nn.Conv2d(mid, channels, kernel_size=1, bias=False))
        self.sigmoid = nn.Sigmoid()
        self.spatial = nn.Sequential(nn.Conv2d(2, 1, kernel_size=7, padding=3, bias=False), nn.BatchNorm2d(1), nn.Sigmoid())
    def forward(self, x):
        avg = torch.mean(x, dim=(2,3), keepdim=True); mx = torch.amax(x, dim=(2,3), keepdim=True)
        ca = self.sigmoid(self.mlp(avg) + self.mlp(mx)); x = x * ca
        avg_sp = torch.mean(x, dim=1, keepdim=True); mx_sp = torch.max(x, dim=1, keepdim=True)[0]
        sa = self.spatial(torch.cat([avg_sp, mx_sp], dim=1)); return x * sa


class SEBlock(nn.Module):
    def __init__(self, channels: int, reduction: int = 16):
        super().__init__()
        self.avg = nn.AdaptiveAvgPool2d(1)
        self.fc = nn.Sequential(nn.Linear(channels, channels // reduction, bias=False), nn.ReLU(inplace=True), nn.Linear(channels // reduction, channels, bias=False), nn.Sigmoid())
    def forward(self, x):
        b, c, _, _ = x.size(); y = self.avg(x).view(b, c); y = self.fc(y).view(b, c, 1, 1); return x * y.expand_as(x)
