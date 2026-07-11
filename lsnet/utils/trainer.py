# -*- coding: utf-8 -*-
"""
训练引擎
"""
import torch
import torch.nn as nn
from torch.cuda.amp import autocast, GradScaler
from .metrics import AverageMeter, calculate_metrics


def train_one_epoch(model, dataloader, criterion, optimizer, scaler, device, scheduler=None):
    """训练一个 epoch"""
    model.train()
    loss_meter = AverageMeter()
    correct = 0
    total = 0

    for images, labels in dataloader:
        images = images.to(device)
        labels = labels.to(device)

        optimizer.zero_grad()

        with autocast():
            outputs = model(images)
            loss = criterion(outputs, labels)

        scaler.scale(loss).backward()
        scaler.step(optimizer)
        scaler.update()

        if scheduler is not None:
            scheduler.step()

        loss_meter.update(loss.item(), images.size(0))
        _, predicted = outputs.max(1)
        total += labels.size(0)
        correct += predicted.eq(labels).sum().item()

    return loss_meter.avg, correct / total * 100


@torch.no_grad()
def validate(model, dataloader, criterion, device):
    """验证"""
    model.eval()
    loss_meter = AverageMeter()
    all_preds = []
    all_labels = []

    for images, labels in dataloader:
        images = images.to(device)
        labels = labels.to(device)

        with autocast():
            outputs = model(images)
            loss = criterion(outputs, labels)

        loss_meter.update(loss.item(), images.size(0))
        _, predicted = outputs.max(1)

        all_preds.extend(predicted.cpu().numpy())
        all_labels.extend(labels.cpu().numpy())

    metrics = calculate_metrics(all_labels, all_preds)
    return (
        loss_meter.avg,
        metrics['accuracy'],
        metrics['f1'],
        all_preds,
        all_labels
    )
