# -*- coding: utf-8 -*-
"""
评估指标
"""
import torch
import numpy as np
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    classification_report, confusion_matrix
)


class AverageMeter:
    """计算并存储平均值和当前值"""
    def __init__(self):
        self.reset()

    def reset(self):
        self.val = 0
        self.avg = 0
        self.sum = 0
        self.count = 0

    def update(self, val, n=1):
        self.val = val
        self.sum += val * n
        self.count += n
        self.avg = self.sum / self.count


def calculate_metrics(y_true, y_pred, average='macro'):
    """计算分类指标"""
    return {
        'accuracy': accuracy_score(y_true, y_pred) * 100,
        'precision': precision_score(y_true, y_pred, average=average, zero_division=0) * 100,
        'recall': recall_score(y_true, y_pred, average=average, zero_division=0) * 100,
        'f1': f1_score(y_true, y_pred, average=average, zero_division=0) * 100,
    }


def get_classification_report(y_true, y_pred, target_names):
    """生成分类报告"""
    return classification_report(y_true, y_pred, target_names=target_names, digits=4)


def get_confusion_matrix(y_true, y_pred):
    """生成混淆矩阵"""
    return confusion_matrix(y_true, y_pred)
