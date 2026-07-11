# -*- coding: utf-8 -*-
"""
LSNet 指数移动平均（EMA）模块

提供模型参数的指数移动平均，用于提升训练稳定性和泛化能力。
"""

import torch


class EMA:
    def __init__(self, model, decay=0.999):
        self.ema = [p.detach().clone() for p in model.parameters()]
        self.decay = decay
        self.model = model

    def update(self):
        for ema_p, p in zip(self.ema, self.model.parameters()):
            ema_p.data = self.decay * ema_p.data + (1 - self.decay) * p.data.detach()

    def apply(self):
        original = []
        for ema_p, p in zip(self.ema, self.model.parameters()):
            original.append(p.data.clone())
            p.data.copy_(ema_p.data)
        return original

    def restore(self, original):
        for p, orig in zip(self.model.parameters(), original):
            p.data.copy_(orig)
