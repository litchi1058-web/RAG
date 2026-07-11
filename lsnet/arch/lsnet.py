# -*- coding: utf-8 -*-
"""
LSNet 模型主体（CVPR 2025, Tsinghua）

官方架构：https://github.com/THU-MIG/lsnet
替换 timm / triton 依赖为纯 PyTorch 实现
"""
import math
import itertools
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.nn.init import trunc_normal_


# ============================================================
#  基础组件（替代 timm）
# ============================================================

class Conv2d_BN(nn.Sequential):
    """Conv2d + BatchNorm，子模块命名为 'c' 和 'bn'（匹配官方 state_dict）"""
    def __init__(self, a, b, ks=1, stride=1, pad=0, dilation=1,
                 groups=1, bn_weight_init=1):
        super().__init__()
        self.add_module('c', nn.Conv2d(a, b, ks, stride, pad, dilation, groups, bias=False))
        self.add_module('bn', nn.BatchNorm2d(b))
        nn.init.constant_(self.bn.weight, bn_weight_init)
        nn.init.constant_(self.bn.bias, 0)


class BN_Linear(nn.Sequential):
    """BN1d + Linear，子模块命名为 'bn' 和 'l'"""
    def __init__(self, a, b, bias=True, std=0.02):
        super().__init__()
        self.add_module('bn', nn.BatchNorm1d(a))
        self.add_module('l', nn.Linear(a, b, bias=bias))
        trunc_normal_(self.l.weight, std=std)
        if bias:
            nn.init.constant_(self.l.bias, 0)


class Residual(nn.Module):
    """残差连接包装器"""
    def __init__(self, m, drop=0.):
        super().__init__()
        self.m = m
        self.drop = drop

    def forward(self, x):
        if self.training and self.drop > 0:
            mask = torch.rand(x.size(0), 1, 1, 1, device=x.device).ge_(self.drop)
            return x + self.m(x) * mask.div(1 - self.drop).detach()
        return x + self.m(x)


class SqueezeExcite(nn.Module):
    """SE 模块（匹配 timm 命名 fc1/fc2）"""
    def __init__(self, dim, rd_ratio=0.25):
        super().__init__()
        rd = max(4, int(dim * rd_ratio))
        self.fc1 = nn.Conv2d(dim, rd, 1, bias=True)
        self.act = nn.ReLU()
        self.fc2 = nn.Conv2d(rd, dim, 1, bias=True)
        self.gate = nn.Sigmoid()

    def forward(self, x):
        s = x.mean((2, 3), keepdim=True)
        s = self.act(self.fc1(s))
        s = self.gate(self.fc2(s))
        return x * s


# ============================================================
#  RepVGG 风格深度卷积
# ============================================================

class RepVGGDW(nn.Module):
    """RepVGG 风格深度卷积：3x3 + 1x1 + identity"""
    def __init__(self, ed):
        super().__init__()
        self.conv = Conv2d_BN(ed, ed, ks=3, stride=1, pad=1, groups=ed)
        self.conv1 = Conv2d_BN(ed, ed, ks=1, stride=1, pad=0, groups=ed)

    def forward(self, x):
        return self.conv(x) + self.conv1(x) + x


# ============================================================
#  FFN（前馈网络）
# ============================================================

class FFN(nn.Module):
    """MLP: pw1 -> ReLU -> pw2"""
    def __init__(self, ed, h):
        super().__init__()
        self.pw1 = Conv2d_BN(ed, h)
        self.act = nn.ReLU()
        self.pw2 = Conv2d_BN(h, ed, bn_weight_init=0)

    def forward(self, x):
        return self.pw2(self.act(self.pw1(x)))


# ============================================================
#  Attention（相对位置偏置多头注意力）
# ============================================================

class Attention(nn.Module):
    """多头自注意力 + 相对位置偏置"""
    def __init__(self, dim, key_dim, num_heads=8, attn_ratio=4, resolution=14):
        super().__init__()
        self.num_heads = num_heads
        self.scale = key_dim ** -0.5
        self.key_dim = key_dim
        self.nh_kd = nh_kd = key_dim * num_heads
        self.d = int(attn_ratio * key_dim)
        self.dh = int(attn_ratio * key_dim) * num_heads
        self.attn_ratio = attn_ratio
        h = self.dh + nh_kd * 2
        self.qkv = Conv2d_BN(dim, h, ks=1)
        self.proj = nn.Sequential(
            nn.ReLU(),
            Conv2d_BN(self.dh, dim, bn_weight_init=0)
        )
        self.dw = Conv2d_BN(nh_kd, nh_kd, ks=3, stride=1, pad=1, groups=nh_kd)

        # 相对位置偏置（支持动态分辨率）
        # 预定义所有可能的偏移类型（基于最大可能分辨率）
        max_offset = resolution * 2  # 支持更大的偏移范围
        attention_offsets = {}
        for i in range(max_offset):
            for j in range(max_offset):
                attention_offsets[(i, j)] = len(attention_offsets)
        self.attention_biases = nn.Parameter(torch.zeros(num_heads, len(attention_offsets)))
        self.attention_offsets = attention_offsets  # 存储偏移映射

    def _get_bias_idxs(self, H, W, device):
        """动态计算当前分辨率的位置偏置索引"""
        points = list(itertools.product(range(H), range(W)))
        N = len(points)
        idxs = []
        for p1 in points:
            for p2 in points:
                offset = (abs(p1[0] - p2[0]), abs(p1[1] - p2[1]))
                # 如果偏移不在预定义范围内，使用最接近的偏移
                idx = self.attention_offsets.get(offset, 0)
                idxs.append(idx)
        return torch.LongTensor(idxs).view(N, N).to(device)

    def forward(self, x):
        B, _, H, W = x.shape
        N = H * W
        qkv = self.qkv(x)
        q, k, v = qkv.view(B, -1, H, W).split([self.nh_kd, self.nh_kd, self.dh], dim=1)
        q = self.dw(q)
        q = q.view(B, self.num_heads, -1, N)
        k = k.view(B, self.num_heads, -1, N)
        v = v.view(B, self.num_heads, -1, N)
        attn = (q.transpose(-2, -1) @ k) * self.scale
        
        # 动态获取当前分辨率的位置偏置
        bias_idxs = self._get_bias_idxs(H, W, x.device)
        bias = self.attention_biases[:, bias_idxs]
        attn = (attn + bias).softmax(dim=-1)
        
        x = (v @ attn.transpose(-2, -1)).reshape(B, -1, H, W)
        x = self.proj(x)
        return x


# ============================================================
#  LKP（大核感知）+ SKA（小核聚合）= LSConv
# ============================================================

class LKP(nn.Module):
    """Large Kernel Perception：生成逐位置卷积核权重"""
    def __init__(self, dim, lks, sks, groups):
        super().__init__()
        self.cv1 = Conv2d_BN(dim, dim // 2)
        self.act = nn.ReLU()
        self.cv2 = Conv2d_BN(dim // 2, dim // 2, ks=lks,
                             pad=(lks - 1) // 2, groups=dim // 2)
        self.cv3 = Conv2d_BN(dim // 2, dim // 2)
        self.cv4 = nn.Conv2d(dim // 2, sks ** 2 * dim // groups, kernel_size=1)
        self.norm = nn.GroupNorm(num_groups=dim // groups,
                                 num_channels=sks ** 2 * dim // groups)
        self.sks = sks
        self.groups = groups
        self.dim = dim

    def forward(self, x):
        x = self.act(self.cv3(self.cv2(self.act(self.cv1(x)))))
        w = self.norm(self.cv4(x))
        B, _, H, W = w.shape
        w = w.view(B, self.dim // self.groups, self.sks ** 2, H, W)
        return w


class SKA(nn.Module):
    """Small Kernel Aggregation（纯 PyTorch 实现，替代 Triton）"""
    def forward(self, x, w):
        B, C, H, W = x.shape
        _, wc, k2, _, _ = w.shape
        ks = int(math.isqrt(k2))
        pad = (ks - 1) // 2
        g = C // wc  # groups

        # unfold: (B, C, ks*ks, H*W)
        x_unf = F.unfold(x, ks, padding=pad).view(B, g, wc, k2, H * W)
        w_flat = w.view(B, 1, wc, k2, H * W)
        out = (x_unf * w_flat).sum(dim=3).view(B, C, H, W)
        return out


class LSConv(nn.Module):
    """Large-Small Convolution（大核感知 + 小核聚合 + 残差）"""
    def __init__(self, dim):
        super().__init__()
        self.lkp = LKP(dim, lks=7, sks=3, groups=8)
        self.ska = SKA()
        self.bn = nn.BatchNorm2d(dim)

    def forward(self, x):
        return self.bn(self.ska(x, self.lkp(x))) + x


# ============================================================
#  Block
# ============================================================

class Block(nn.Module):
    """LSNet 基本块
    - 偶数深度: RepVGGDW + SE + FFN
    - 奇数深度: LSConv (stage<3) / Attention (stage=3) + FFN
    """
    def __init__(self, ed, kd, nh=8, ar=4, resolution=14, stage=-1, depth=-1):
        super().__init__()
        if depth % 2 == 0:
            self.mixer = RepVGGDW(ed)
            self.se = SqueezeExcite(ed, 0.25)
        else:
            self.se = nn.Identity()
            if stage == 3:
                self.mixer = Residual(Attention(ed, kd, nh, ar, resolution=resolution))
            else:
                self.mixer = LSConv(ed)
        self.ffn = Residual(FFN(ed, int(ed * 2)))

    def forward(self, x):
        return self.ffn(self.se(self.mixer(x)))


# ============================================================
#  LSNet 主网络
# ============================================================

class LSNet(nn.Module):
    """
    LSNet: See Large, Focus Small (CVPR 2025, Tsinghua)

    配置参数与官方 lsnet_t 一致：
      embed_dim=[64, 128, 256, 384]
      depth=[0, 2, 8, 10]
      num_heads=[3, 3, 3, 4]
      patch_size=8
    """
    def __init__(self, img_size=224, patch_size=8, in_chans=3,
                 num_classes=9,
                 embed_dim=None, key_dim=None,
                 depth=None, num_heads=None):
        super().__init__()

        # lsnet_t 默认配置
        if embed_dim is None:
            embed_dim = [64, 128, 256, 384]
        if key_dim is None:
            key_dim = [16, 16, 16, 16]
        if depth is None:
            depth = [0, 2, 8, 10]
        if num_heads is None:
            num_heads = [3, 3, 3, 4]

        self.num_classes = num_classes
        self.num_features = embed_dim[-1]

        # patch embedding: 3 层 stride=2 卷积 3→16→32→64
        self.patch_embed = nn.Sequential(
            Conv2d_BN(in_chans, embed_dim[0] // 4, ks=3, stride=2, pad=1),
            nn.ReLU(),
            Conv2d_BN(embed_dim[0] // 4, embed_dim[0] // 2, ks=3, stride=2, pad=1),
            nn.ReLU(),
            Conv2d_BN(embed_dim[0] // 2, embed_dim[0], ks=3, stride=2, pad=1)
        )

        resolution = img_size // patch_size
        attn_ratio = [embed_dim[i] / (key_dim[i] * num_heads[i])
                      for i in range(len(embed_dim))]

        self.blocks1 = nn.Sequential()
        self.blocks2 = nn.Sequential()
        self.blocks3 = nn.Sequential()
        self.blocks4 = nn.Sequential()
        blocks = [self.blocks1, self.blocks2, self.blocks3, self.blocks4]

        for i, (ed, kd, dpth, nh, ar) in enumerate(
                zip(embed_dim, key_dim, depth, num_heads, attn_ratio)):
            for d in range(dpth):
                blocks[i].append(Block(ed, kd, nh, ar, resolution, stage=i, depth=d))

            # 下采样（追加到下一个 stage 开头）
            if i != len(depth) - 1:
                blk = blocks[i + 1]
                resolution_ = (resolution - 1) // 2 + 1
                blk.append(Conv2d_BN(embed_dim[i], embed_dim[i],
                                     ks=3, stride=2, pad=1, groups=embed_dim[i]))
                blk.append(Conv2d_BN(embed_dim[i], embed_dim[i + 1],
                                     ks=1, stride=1, pad=0))
                resolution = resolution_

        # 分类头
        self.head = BN_Linear(embed_dim[-1], num_classes)

    def forward(self, x):
        x = self.patch_embed(x)
        x = self.blocks1(x)
        x = self.blocks2(x)
        x = self.blocks3(x)
        x = self.blocks4(x)
        x = F.adaptive_avg_pool2d(x, 1).flatten(1)
        x = self.head(x)
        return x
