# -*- coding: utf-8 -*-
"""
LSNet 损失函数模块

提供 Focal Loss 和知识蒸馏损失（DistillationLoss）实现。
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


class FocalLoss(nn.Module):
    def __init__(self, alpha=None, gamma=2.0, reduction='mean'):
        super(FocalLoss, self).__init__()
        self.gamma = gamma
        self.alpha = alpha
        self.reduction = reduction

    def forward(self, inputs, targets):
        ce_loss = nn.CrossEntropyLoss(reduction='none')(inputs, targets)
        pt = torch.exp(-ce_loss)
        focal_loss = ((1 - pt) ** self.gamma) * ce_loss

        if self.alpha is not None:
            if self.alpha.dim() == 1:
                alpha = self.alpha[targets]
            focal_loss = alpha * focal_loss

        if self.reduction == 'mean':
            return focal_loss.mean()
        elif self.reduction == 'sum':
            return focal_loss.sum()
        else:
            return focal_loss


class DistillationLoss(nn.Module):
    def __init__(self, alpha=0.5, temperature=4.0, hard_criterion=None):
        super().__init__()
        self.alpha = alpha
        self.temperature = temperature
        self.hard_criterion = hard_criterion if hard_criterion is not None else nn.CrossEntropyLoss()
        self.kl_div = nn.KLDivLoss(reduction='batchmean')

    def forward(self, student_logits, teacher_logits, labels):
        teacher_probs = F.softmax(teacher_logits / self.temperature, dim=1)
        student_probs = F.log_softmax(student_logits / self.temperature, dim=1)
        distill_loss = self.kl_div(student_probs, teacher_probs) * (self.temperature ** 2)
        hard_loss = self.hard_criterion(student_logits, labels)
        total_loss = self.alpha * distill_loss + (1 - self.alpha) * hard_loss
        return total_loss, distill_loss, hard_loss
