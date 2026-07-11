# -*- coding: utf-8 -*-
"""
LSNet 训练入口（5 折交叉验证 + MixUp/CutMix + CBAM 注意力 + 知识蒸馏）

功能特性：
  - 直接读取 训练集/测试集 目录（简洁可靠）
  - MixUp / CutMix 批级别混合增强（支持单独控制）
  - RandAugment 自动增强
  - Test-Time Augmentation（测试时增强）
  - Stochastic Weight Averaging（SWA）
  - WeightedRandomSampler + 类别权重损失
  - CBAM 注意力（可选）
  - CosineAnnealingLR + 梯度裁剪 + AMP + Warmup
  - 混淆矩阵 + 分类报告 + 可视化
  - 5 折 StratifiedKFold 交叉验证
  - 早停机制（支持验证集/测试集）
  - 知识蒸馏（教师模型：VGG19 + CBAM + SE）
  - EMA（指数移动平均）
  - Top-k 准确率评估
  - TensorBoard 日志
  - 训练曲线可视化
  - 模型恢复训练
  - 模型导出（ONNX格式）
  - 学习率查找器
  - 标签平滑
  - Focal Loss
"""
import os
import sys
import argparse
import random
import json
import datetime
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader, WeightedRandomSampler
from torch.cuda.amp import GradScaler
from torch.optim import swa_utils
from torchvision import transforms
from torchvision.transforms import RandAugment as TVRandAugment
from torch.utils.tensorboard import SummaryWriter
from PIL import Image
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.metrics import classification_report, confusion_matrix, f1_score, accuracy_score

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from lsnet.arch import build_model
from backend.shared.paths import get_train_logs_dir, get_checkpoints_dir, get_results_dir, get_raw_data_dir
from backend.shared.constants import IMG_SIZE, IMG_MEAN, IMG_STD

from lsnet.arch.attention import CBAM, SEBlock
from lsnet.arch.teachers import VGG19CBAM
from lsnet.data.dataset import FruitDiseaseDataset
from lsnet.utils.metrics import AverageMeter
from lsnet.utils.losses import FocalLoss, DistillationLoss
from lsnet.utils.ema import EMA


def get_train_transform(image_size=IMG_SIZE, strong_aug=False, use_randaugment=False, randaugment_n=2, randaugment_m=9):
    base_transforms = [
        transforms.Resize((image_size + 32, image_size + 32)),
    ]

    if use_randaugment:
        base_transforms.extend([
            transforms.RandomResizedCrop(image_size, scale=(0.7, 1.0) if strong_aug else (0.85, 1.0)),
            transforms.RandomHorizontalFlip(p=0.5),
        ])
        try:
            base_transforms.append(TVRandAugment(num_ops=randaugment_n, magnitude=randaugment_m))
        except TypeError:
            # 兼容旧版 torchvision v1 API
            base_transforms.append(TVRandAugment(num_ops=randaugment_n))
    elif strong_aug:
        base_transforms.extend([
            transforms.RandomResizedCrop(image_size, scale=(0.7, 1.0)),
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.RandomVerticalFlip(p=0.3),
            transforms.RandomRotation(30),
            transforms.RandomAffine(degrees=0, translate=(0.1, 0.1), scale=(0.9, 1.1)),
            transforms.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.2, hue=0.1),
            transforms.RandomPerspective(distortion_scale=0.2, p=0.3),
            transforms.GaussianBlur(kernel_size=(3, 3), sigma=(0.1, 2.0)),
        ])
    else:
        base_transforms.extend([
            transforms.RandomResizedCrop(image_size, scale=(0.85, 1.0)),
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.RandomVerticalFlip(p=0.2),
            transforms.RandomRotation(15),
            transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.15, hue=0.05),
        ])

    base_transforms.extend([
        transforms.ToTensor(),
        transforms.RandomErasing(p=0.3 if strong_aug else 0.2),
        transforms.Normalize(IMG_MEAN, IMG_STD),
    ])

    return transforms.Compose(base_transforms)


def get_val_transform(image_size=IMG_SIZE):
    return transforms.Compose([
        transforms.Resize((image_size + 32, image_size + 32)),
        transforms.CenterCrop(image_size),
        transforms.ToTensor(),
        transforms.Normalize(IMG_MEAN, IMG_STD),
    ])


def load_paths_labels(root_dir):
    root = Path(root_dir)
    paths, labels = [], []
    class_names = sorted([d.name for d in root.iterdir() if d.is_dir()])
    for idx, cls_name in enumerate(class_names):
        cls_dir = root / cls_name
        for p in cls_dir.iterdir():
            if p.suffix.lower() in {'.jpg', '.jpeg', '.png', '.bmp'}:
                paths.append(str(p))
                labels.append(idx)
    return paths, labels, class_names


def load_plantvillage_for_training(plantvillage_dir, class_names_union):
    pv_root = Path(plantvillage_dir)
    if not pv_root.exists():
        return [], []

    paths, labels = [], []
    for pv_cls_dir in pv_root.iterdir():
        if not pv_cls_dir.is_dir():
            continue
        pv_cls_name = pv_cls_dir.name
        matched = False
        for i, cn in enumerate(class_names_union):
            if pv_cls_name == cn or pv_cls_name in cn or cn in pv_cls_name:
                for p in pv_cls_dir.glob('*.jpg'):
                    paths.append(str(p))
                    labels.append(i)
                matched = True
                break
        if not matched:
            print(f"  [PlantVillage] 跳过未匹配类别: {pv_cls_name}")
    return paths, labels


def compute_class_weights(labels, n_classes, beta=0.9999):
    cnt = np.bincount(labels, minlength=n_classes).astype(np.float64)
    effective = 1.0 - np.power(beta, cnt)
    w = (1.0 - beta) / (effective + 1e-12)
    w = w / np.sum(w) * n_classes
    return torch.tensor(w, dtype=torch.float)


def mixup_cutmix_collate(batch, mixup_alpha=0.2, mixup_prob=0.5, cutmix_alpha=0.0, cutmix_prob=0.5):
    imgs, lbls = zip(*batch)
    imgs = torch.stack(imgs)
    lbls = torch.tensor(lbls, dtype=torch.long)

    use_mixup = mixup_alpha > 0.0
    use_cutmix = cutmix_alpha > 0.0

    if not use_mixup and not use_cutmix:
        return imgs, lbls, None, 1.0, 'none'

    if use_mixup and use_cutmix:
        do_mixup = random.random() < 0.5
    else:
        do_mixup = use_mixup

    if do_mixup:
        if random.random() > mixup_prob:
            return imgs, lbls, None, 1.0, 'none'
        B = imgs.size(0)
        idx = torch.randperm(B)
        lam = np.random.beta(mixup_alpha, mixup_alpha)
        mixed = lam * imgs + (1.0 - lam) * imgs[idx]
        return mixed, lbls, lbls[idx], lam, 'mixup'
    else:
        if random.random() > cutmix_prob:
            return imgs, lbls, None, 1.0, 'none'
        B = imgs.size(0)
        idx = torch.randperm(B)
        lam = np.random.beta(cutmix_alpha, cutmix_alpha)
        _, _, H, W = imgs.shape
        cut_rat = np.sqrt(1.0 - lam)
        cut_w, cut_h = int(W * cut_rat), int(H * cut_rat)
        cx, cy = np.random.randint(W), np.random.randint(H)
        x1 = np.clip(cx - cut_w // 2, 0, W)
        x2 = np.clip(cx + cut_w // 2, 0, W)
        y1 = np.clip(cy - cut_h // 2, 0, H)
        y2 = np.clip(cy + cut_h // 2, 0, H)
        imgs[:, :, y1:y2, x1:x2] = imgs[idx, :, y1:y2, x1:x2]
        lam = 1.0 - ((x2 - x1) * (y2 - y1) / (W * H))
        return imgs, lbls, lbls[idx], lam, 'cutmix'


def make_collate_fn(mixup_alpha=0.0, mixup_prob=0.5, cutmix_alpha=0.0, cutmix_prob=0.5):
    return lambda batch: mixup_cutmix_collate(batch, mixup_alpha=mixup_alpha, mixup_prob=mixup_prob, cutmix_alpha=cutmix_alpha, cutmix_prob=cutmix_prob)





def set_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def find_lr(model, train_loader, optimizer, criterion, device, init_lr=1e-7, final_lr=10.0, beta=0.98):
    num_iter = len(train_loader)
    lr_step = (final_lr / init_lr) ** (1 / num_iter)
    
    model.train()
    optimizer.param_groups[0]['lr'] = init_lr
    
    avg_loss = 0.0
    best_loss = float('inf')
    losses = []
    lrs = []
    
    for i, batch in enumerate(train_loader):
        if len(batch) == 5:
            images, labels_a, labels_b, lam, _ = batch
        else:
            images, labels_a = batch
            labels_b, lam = None, 1.0
        
        images = images.to(device, non_blocking=True)
        labels_a = labels_a.to(device, non_blocking=True)
        
        optimizer.zero_grad()
        
        with torch.amp.autocast('cuda'):
            outputs = model(images)
            if labels_b is None:
                loss = criterion(outputs, labels_a)
            else:
                loss = lam * criterion(outputs, labels_a) + (1.0 - lam) * criterion(outputs, labels_b)
        
        avg_loss = beta * avg_loss + (1 - beta) * loss.item()
        smoothed_loss = avg_loss / (1 - beta ** (i + 1))
        
        losses.append(smoothed_loss)
        lrs.append(optimizer.param_groups[0]['lr'])
        
        if smoothed_loss > 4 * best_loss:
            break
        
        if smoothed_loss < best_loss:
            best_loss = smoothed_loss
        
        loss.backward()
        optimizer.step()
        
        optimizer.param_groups[0]['lr'] *= lr_step
    
    if len(losses) > 10:
        grads = np.gradient(losses)
        best_idx = np.argmin(grads[10:-10]) + 10
        best_lr = lrs[best_idx]
    else:
        best_lr = 1e-3
    
    return best_lr, lrs, losses


def train_one_epoch(model, dataloader, criterion, optimizer, scaler, device, clip_grad=1.0, 
                    teacher_model=None, distill_criterion=None, ema=None):
    model.train()
    if teacher_model is not None:
        teacher_model.eval()
    
    loss_meter = AverageMeter()
    distill_loss_meter = AverageMeter()
    hard_loss_meter = AverageMeter()
    correct, total = 0, 0

    for batch in dataloader:
        if len(batch) == 5:
            images, labels_a, labels_b, lam, _ = batch
        else:
            images, labels_a = batch
            labels_b, lam = None, 1.0

        images = images.to(device, non_blocking=True)
        labels_a = labels_a.to(device, non_blocking=True)
        if labels_b is not None:
            labels_b = labels_b.to(device, non_blocking=True)

        optimizer.zero_grad(set_to_none=True)

        with torch.amp.autocast('cuda'):
            outputs = model(images)
            
            if distill_criterion is not None and teacher_model is not None:
                with torch.no_grad():
                    teacher_outputs = teacher_model(images)
                
                if labels_b is None:
                    loss, distill_loss, hard_loss = distill_criterion(outputs, teacher_outputs, labels_a)
                else:
                    teacher_probs = F.softmax(teacher_outputs / distill_criterion.temperature, dim=1)
                    student_probs = F.log_softmax(outputs / distill_criterion.temperature, dim=1)
                    distill_loss = distill_criterion.kl_div(student_probs, teacher_probs) * (distill_criterion.temperature ** 2)
                    
                    hard_loss = distill_criterion.hard_criterion(outputs, labels_a) * lam + \
                                distill_criterion.hard_criterion(outputs, labels_b) * (1.0 - lam)
                    
                    loss = distill_criterion.alpha * distill_loss + (1 - distill_criterion.alpha) * hard_loss
                
                distill_loss_meter.update(distill_loss.item(), images.size(0))
                hard_loss_meter.update(hard_loss.item(), images.size(0))
            else:
                if labels_b is None:
                    loss = criterion(outputs, labels_a)
                else:
                    loss = lam * criterion(outputs, labels_a) + (1.0 - lam) * criterion(outputs, labels_b)

        scaler.scale(loss).backward()
        scaler.unscale_(optimizer)
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=clip_grad)
        scaler.step(optimizer)
        scaler.update()

        if ema is not None:
            ema.update()

        loss_meter.update(loss.item(), images.size(0))
        _, pred = outputs.max(1)
        if labels_b is None:
            correct += (pred == labels_a).sum().item()
            total += labels_a.size(0)
        else:
            correct += (lam * (pred == labels_a).float() + (1.0 - lam) * (pred == labels_b).float()).sum().item()
            total += labels_a.size(0)

    return loss_meter.avg, correct / total * 100.0, distill_loss_meter.avg, hard_loss_meter.avg


@torch.no_grad()
def validate(model, dataloader, criterion, device, ema=None):
    model.eval()
    
    if ema is not None:
        original = ema.apply()
    
    loss_meter = AverageMeter()
    all_preds, all_labels = [], []
    all_probs = []

    for images, labels in dataloader:
        images = images.to(device, non_blocking=True)
        labels = labels.to(device, non_blocking=True)

        with torch.amp.autocast('cuda'):
            outputs = model(images)
            loss = criterion(outputs, labels)
            probs = F.softmax(outputs, dim=1)

        loss_meter.update(loss.item(), images.size(0))
        _, pred = outputs.max(1)
        all_preds.extend(pred.cpu().numpy())
        all_labels.extend(labels.cpu().numpy())
        all_probs.extend(probs.cpu().numpy())

    if ema is not None:
        ema.restore(original)

    acc = accuracy_score(all_labels, all_preds) * 100.0
    f1 = f1_score(all_labels, all_preds, average='macro', zero_division=0) * 100.0
    
    return loss_meter.avg, acc, f1, all_preds, all_labels, all_probs


@torch.no_grad()
def validate_with_tta(model, dataloader, criterion, device, ema=None, tta_flips=True):
    """Test-Time Augmentation: run validation with horizontal flip averaging"""
    model.eval()
    if ema is not None:
        original = ema.apply()

    loss_meter = AverageMeter()
    all_preds, all_labels = [], []
    all_probs = []

    for images, labels in dataloader:
        images = images.to(device, non_blocking=True)
        labels = labels.to(device, non_blocking=True)

        with torch.amp.autocast('cuda'):
            outputs = model(images)
            probs = F.softmax(outputs, dim=1)

            if tta_flips:
                # Horizontal flip TTA
                flipped = torch.flip(images, dims=[3])
                flip_outputs = model(flipped)
                flip_probs = F.softmax(flip_outputs, dim=1)
                probs = (probs + flip_probs) / 2.0

            loss = criterion(outputs, labels)

        loss_meter.update(loss.item(), images.size(0))
        _, pred = probs.max(1)
        all_preds.extend(pred.cpu().numpy())
        all_labels.extend(labels.cpu().numpy())
        all_probs.extend(probs.cpu().numpy())

    if ema is not None:
        ema.restore(original)

    acc = accuracy_score(all_labels, all_preds) * 100.0
    f1 = f1_score(all_labels, all_preds, average='macro', zero_division=0) * 100.0
    return loss_meter.avg, acc, f1, all_preds, all_labels, all_probs


@torch.no_grad()
def compute_top_k_acc(all_probs, all_labels, k=3):
    probs = np.array(all_probs)
    labels = np.array(all_labels)
    top_k = np.argsort(probs, axis=1)[:, -k:]
    correct = np.mean([labels[i] in top_k[i] for i in range(len(labels))])
    return correct * 100.0


def plot_confusion_matrix(cm, class_names, save_path):
    plt.figure(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=class_names, yticklabels=class_names)
    plt.xlabel('预测')
    plt.ylabel('真实')
    plt.title('Confusion Matrix')
    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    plt.close()


def plot_training_curves(train_history, save_path):
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    
    axes[0].plot(train_history['train_loss'], label='Train')
    axes[0].plot(train_history['val_loss'], label='Val')
    axes[0].set_xlabel('Epoch')
    axes[0].set_ylabel('Loss')
    axes[0].set_title('Loss Curve')
    axes[0].legend()
    axes[0].grid(True)
    
    axes[1].plot(train_history['train_acc'], label='Train')
    axes[1].plot(train_history['val_acc'], label='Val')
    if 'test_acc' in train_history and isinstance(train_history['test_acc'], list):
        test_epochs = range(1, len(train_history['train_acc']) + 1)
        axes[1].plot(test_epochs, train_history['test_acc'], label='Test', marker='o')
    axes[1].set_xlabel('Epoch')
    axes[1].set_ylabel('Accuracy (%)')
    axes[1].set_title('Accuracy Curve')
    axes[1].legend()
    axes[1].grid(True)
    
    axes[2].plot(train_history['val_f1'], label='Val F1')
    axes[2].set_xlabel('Epoch')
    axes[2].set_ylabel('F1 Score (%)')
    axes[2].set_title('F1 Curve')
    axes[2].legend()
    axes[2].grid(True)
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    plt.close()


def get_timestamp():
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


def save_results_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def export_model_to_onnx(model, device, input_size, save_path):
    dummy_input = torch.randn(1, 3, input_size, input_size).to(device)
    model.eval()
    with torch.no_grad():
        torch.onnx.export(
            model,
            dummy_input,
            str(save_path),
            opset_version=13,
            do_constant_folding=True,
            input_names=['input'],
            output_names=['output'],
            dynamic_axes={'input': {0: 'batch_size'}, 'output': {0: 'batch_size'}}
        )


def train_model(model, train_loader, val_loader, test_loader, criterion, optimizer, scheduler, scaler, 
                args, device, class_names, ckpt_dir, log_fn, writer=None, teacher_model=None, distill_criterion=None):
    ema = EMA(model, decay=0.999) if args.use_ema else None
    
    best_val_acc = 0.0
    best_test_acc = 0.0
    best_epoch = 0
    patience = 0
    
    train_history = {'train_loss': [], 'train_acc': [], 'val_loss': [], 'val_acc': [], 'val_f1': [], 'test_acc': []}

    for epoch in range(1, args.epochs + 1):
        current_lr = optimizer.param_groups[0]['lr']
        
        tr_loss, tr_acc, distill_loss, hard_loss = train_one_epoch(
            model, train_loader, criterion, optimizer, scaler, device,
            clip_grad=args.grad_clip,
            teacher_model=teacher_model,
            distill_criterion=distill_criterion,
            ema=ema
        )
        scheduler.step()
        val_loss, val_acc, val_f1, _, _, _ = validate(model, val_loader, criterion, device, ema)

        train_history['train_loss'].append(tr_loss)
        train_history['train_acc'].append(tr_acc)
        train_history['val_loss'].append(val_loss)
        train_history['val_acc'].append(val_acc)
        train_history['val_f1'].append(val_f1)

        if writer:
            writer.add_scalar('Loss/Train', tr_loss, epoch)
            writer.add_scalar('Loss/Val', val_loss, epoch)
            writer.add_scalar('Accuracy/Train', tr_acc, epoch)
            writer.add_scalar('Accuracy/Val', val_acc, epoch)
            writer.add_scalar('F1/Val', val_f1, epoch)
            writer.add_scalar('LearningRate', current_lr, epoch)
            if args.use_distill:
                writer.add_scalar('Loss/Distill', distill_loss, epoch)
                writer.add_scalar('Loss/Hard', hard_loss, epoch)

        if args.use_distill:
            log_fn(f"  [{epoch:03d}/{args.epochs}] lr={current_lr:.6f} | Train: {tr_loss:.4f} loss, {tr_acc:.2f}% acc (distill={distill_loss:.4f}, hard={hard_loss:.4f}) | Val: {val_loss:.4f} loss, {val_acc:.2f}% acc, {val_f1:.2f}% f1")
        else:
            log_fn(f"  [{epoch:03d}/{args.epochs}] lr={current_lr:.6f} | Train: {tr_loss:.4f} loss, {tr_acc:.2f}% acc | Val: {val_loss:.4f} loss, {val_acc:.2f}% acc, {val_f1:.2f}% f1")

        test_acc_epoch = None
        if args.test_freq > 0 and epoch % args.test_freq == 0:
            if args.use_tta:
                test_loss_epoch, test_acc_epoch, test_f1_epoch, _, _, _ = validate_with_tta(model, test_loader, criterion, device, ema)
            else:
                test_loss_epoch, test_acc_epoch, test_f1_epoch, _, _, _ = validate(model, test_loader, criterion, device, ema)
            log_fn(f"    ├── Test: loss={test_loss_epoch:.4f}, acc={test_acc_epoch:.2f}%, f1={test_f1_epoch:.2f}%")
            train_history['test_acc'].append(test_acc_epoch)
            if writer:
                writer.add_scalar('Accuracy/Test', test_acc_epoch, epoch)
                writer.add_scalar('F1/Test', test_f1_epoch, epoch)

        save_best = False
        if args.early_stopping_test and test_acc_epoch is not None:
            if test_acc_epoch > best_test_acc + 0.001:
                best_test_acc = test_acc_epoch
                best_val_acc = val_acc
                best_epoch = epoch
                patience = 0
                save_best = True
                log_fn(f"    ★ 最佳 (Test Acc={best_test_acc:.2f}%)")
            else:
                patience += 1
        else:
            if val_acc > best_val_acc + 0.001:
                best_val_acc = val_acc
                best_epoch = epoch
                patience = 0
                save_best = True
                log_fn(f"    ★ 最佳 (Val Acc={best_val_acc:.2f}%)")
            else:
                patience += 1

        if save_best:
            torch.save({
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'scheduler_state_dict': scheduler.state_dict(),
                'scaler_state_dict': scaler.state_dict(),
                'epoch': epoch,
                'best_acc': best_val_acc,
                'best_test_acc': best_test_acc if args.early_stopping_test else None,
                'config': vars(args),
                'class_names': class_names
            }, ckpt_dir / "best_model.pth")

        if epoch % 20 == 0:
            torch.save({
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'scheduler_state_dict': scheduler.state_dict(),
                'scaler_state_dict': scaler.state_dict(),
                'epoch': epoch,
                'config': vars(args)
            }, ckpt_dir / f"checkpoint_epoch_{epoch}.pth")

        if patience >= args.patience:
            log_fn(f"    ■ 早停 @ epoch {epoch}")
            break

    # SWA: Stochastic Weight Averaging after main loop
    if args.use_swa:
        log_fn(f"\n  启动 SWA 微调（{args.swa_epochs} epochs, lr={args.swa_lr}）...")
        swa_model = swa_utils.AveragedModel(model)
        swa_scheduler = swa_utils.SWALR(optimizer, swa_lr=args.swa_lr)
        for swa_epoch in range(args.swa_epochs):
            tr_loss, tr_acc, _, _ = train_one_epoch(
                model, train_loader, criterion, optimizer, scaler, device,
                clip_grad=args.grad_clip,
                teacher_model=teacher_model,
                distill_criterion=distill_criterion,
                ema=ema
            )
            swa_model.update_parameters(model)
            swa_scheduler.step()
            log_fn(f"    SWA [{swa_epoch+1}/{args.swa_epochs}] loss={tr_loss:.4f}, acc={tr_acc:.2f}%")
        swa_utils.update_bn(train_loader, swa_model, device=device)
        model.load_state_dict(swa_model.module.state_dict())
        log_fn(f"  SWA 完成")

    return best_val_acc, best_test_acc, best_epoch, train_history


def create_criterion(args, class_weights, device, log_fn=print):
    if args.use_focal_loss:
        criterion = FocalLoss(
            alpha=class_weights.to(device) if class_weights is not None else None,
            gamma=args.focal_gamma
        )
        log_fn(f"使用 Focal Loss (γ={args.focal_gamma})")
    else:
        criterion = nn.CrossEntropyLoss(
            weight=class_weights.to(device) if class_weights is not None else None,
            label_smoothing=args.label_smoothing
        )
        if args.label_smoothing > 0:
            log_fn(f"使用 Label Smoothing ({args.label_smoothing})")
    return criterion


def create_teacher_and_distill(args, num_classes, device, base_criterion, log_fn=print):
    teacher_model = None
    distill_criterion = None
    if args.use_distill and args.teacher_ckpt:
        teacher_model = VGG19CBAM(num_classes=num_classes, pretrained=False, use_cbam=True, use_se=True)
        teacher_model = teacher_model.to(device)
        ckpt = torch.load(args.teacher_ckpt, map_location=device, weights_only=False)
        teacher_model.load_state_dict(ckpt['model_state_dict'])
        teacher_model.eval()
        distill_criterion = DistillationLoss(
            alpha=args.distill_alpha,
            temperature=args.distill_temp,
            hard_criterion=base_criterion
        )
        log_fn(f"使用知识蒸馏: α={args.distill_alpha}, T={args.distill_temp}")
        log_fn(f"教师模型: VGG19+CBAM+SE")
        log_fn(f"教师权重: {args.teacher_ckpt}")
    return teacher_model, distill_criterion


def create_optimizer_and_scheduler(args, model, num_epochs=None, log_fn=print):
    epochs = num_epochs if num_epochs is not None else args.epochs
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    if args.warmup_epochs > 0:
        warmup_scheduler = torch.optim.lr_scheduler.LinearLR(
            optimizer, start_factor=0.1, total_iters=args.warmup_epochs
        )
        cosine_scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
            optimizer, T_max=epochs - args.warmup_epochs
        )
        scheduler = torch.optim.lr_scheduler.SequentialLR(
            optimizer, schedulers=[warmup_scheduler, cosine_scheduler],
            milestones=[args.warmup_epochs]
        )
        log_fn(f"使用 Warmup ({args.warmup_epochs} epochs) + CosineAnnealing")
    else:
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)
    scaler = GradScaler()
    return optimizer, scheduler, scaler


def build_dataloaders(train_paths, train_labels, val_paths, val_labels, args, num_classes):
    class_weights = compute_class_weights(train_labels, num_classes)
    sample_weights = [class_weights[l].item() for l in train_labels]
    sampler = WeightedRandomSampler(sample_weights, num_samples=len(train_labels), replacement=True)
    train_ds = FruitDiseaseDataset(list(zip(train_paths, train_labels)),
                                   get_train_transform(args.image_size, strong_aug=args.strong_aug,
                                                       use_randaugment=args.use_randaugment,
                                                       randaugment_n=args.randaugment_n,
                                                       randaugment_m=args.randaugment_m))
    val_ds = FruitDiseaseDataset(list(zip(val_paths, val_labels)), get_val_transform(args.image_size))
    collate_fn = make_collate_fn(args.mixup_alpha, args.mixup_prob, args.cutmix_alpha, args.cutmix_prob) if args.use_mixup else None
    train_loader = DataLoader(train_ds, batch_size=args.batch_size, sampler=sampler,
                              num_workers=0, pin_memory=True, collate_fn=collate_fn)
    val_loader = DataLoader(val_ds, batch_size=args.batch_size, shuffle=False,
                            num_workers=0, pin_memory=True)
    return train_loader, val_loader, class_weights


def evaluate_test(model, test_loader, criterion, device, class_names, res_dir, exp_name, log_fn, top_k=3, use_tta=False):
    if use_tta:
        test_loss, test_acc, test_f1, test_preds, test_labels, test_probs = validate_with_tta(model, test_loader, criterion, device)
    else:
        test_loss, test_acc, test_f1, test_preds, test_labels, test_probs = validate(model, test_loader, criterion, device)
    metrics = {'test_loss': test_loss, 'test_acc': test_acc, 'test_f1': test_f1}
    for k in range(2, top_k + 1):
        metrics[f'top{k}_acc'] = compute_top_k_acc(test_probs, test_labels, k=k)
    log_fn(f"Loss: {test_loss:.4f}")
    log_fn(f"Acc:  {test_acc:.2f}%")
    log_fn(f"F1:   {test_f1:.2f}%")
    for k in range(2, top_k + 1):
        log_fn(f"Top-{k}: {metrics[f'top{k}_acc']:.2f}%")
    metrics['preds'] = test_preds
    metrics['trues'] = test_labels
    metrics['probs'] = test_probs
    return metrics


def main():
    parser = argparse.ArgumentParser(description='LSNet 训练（5 折 CV + MixUp/CutMix + CBAM）')
    
    parser.add_argument('--model',         type=str,   default='lsnet',     help='模型名称')
    parser.add_argument('--epochs',        type=int,   default=80,          help='每折训练轮数')
    parser.add_argument('--batch-size',    type=int,   default=32,          help='批次大小')
    parser.add_argument('--lr',            type=float, default=1e-3,        help='初始学习率')
    parser.add_argument('--weight-decay',  type=float, default=1e-4,        help='权重衰减')
    parser.add_argument('--image-size',    type=int,   default=224,         help='图像尺寸')
    parser.add_argument('--exp-suffix',    type=str,   default='',          help='实验名称后缀')
    parser.add_argument('--seed',          type=int,   default=42,          help='随机种子')
    
    parser.add_argument('--use-plantvillage', action='store_true',          help='合并 PlantVillage 数据')
    
    parser.add_argument('--cv-folds',      type=int,   default=5,
                        help='CV 折数（1 则直接训练+测试，不做 CV）')
    parser.add_argument('--skip-final-train', action='store_true',
                        help='CV 结束后不训练最终模型')
    parser.add_argument('--test-freq',     type=int,   default=0,
                        help='测试集评估频率（0=仅在每折结束时测试，1=每个epoch测试）')
    
    parser.add_argument('--use-mixup',     action='store_true',             help='启用 MixUp/CutMix')
    parser.add_argument('--mixup-alpha',   type=float, default=0.2,         help='Beta alpha')
    parser.add_argument('--mixup-prob',    type=float, default=0.5,         help='触发概率')
    parser.add_argument('--cutmix-alpha',  type=float, default=0.0,         help='CutMix alpha（0=不启用单独的 CutMix）')
    parser.add_argument('--cutmix-prob',   type=float, default=0.5,         help='CutMix 触发概率（单独启用时）')

    parser.add_argument('--use-cbam',      action='store_true',             help='启用 CBAM')
    
    parser.add_argument('--patience',      type=int,   default=15,          help='早停 patience')
    parser.add_argument('--early-stopping-test', action='store_true',       help='基于测试集准确率进行早停')
    
    parser.add_argument('--use-focal-loss', action='store_true',            help='使用 Focal Loss')
    parser.add_argument('--focal-gamma',   type=float, default=2.0,         help='Focal Loss gamma')
    parser.add_argument('--find-lr',       action='store_true',             help='先查找最佳学习率')
    parser.add_argument('--freeze-epochs', type=int, default=0,             help='冻结特征提取层训练轮数')
    parser.add_argument('--grad-clip',     type=float, default=1.0,         help='梯度裁剪阈值')
    parser.add_argument('--label-smoothing', type=float, default=0.0,       help='标签平滑系数')
    parser.add_argument('--warmup-epochs', type=int, default=0,             help='学习率预热轮数')
    parser.add_argument('--use-ema',       action='store_true',             help='使用 EMA')

    parser.add_argument('--use-swa',       action='store_true',             help='启用 Stochastic Weight Averaging')
    parser.add_argument('--swa-epochs',    type=int,   default=5,           help='SWA 平均轮数')
    parser.add_argument('--swa-lr',        type=float, default=1e-4,        help='SWA 学习率')

    parser.add_argument('--strong-aug',    action='store_true',             help='启用强数据增强')
    parser.add_argument('--use-randaugment', action='store_true',           help='使用 RandAugment 自动增强（替代手动增强）')
    parser.add_argument('--randaugment-n', type=int,   default=2,           help='RandAugment N (变换数量)')
    parser.add_argument('--randaugment-m', type=int,   default=9,           help='RandAugment M (变换幅度)')

    parser.add_argument('--use-distill',   action='store_true',             help='启用知识蒸馏')
    parser.add_argument('--teacher-ckpt',  type=str,   default='',          help='教师模型权重路径')
    parser.add_argument('--distill-temp',  type=float, default=4.0,         help='蒸馏温度')
    parser.add_argument('--distill-alpha', type=float, default=0.5,         help='蒸馏损失权重')
    
    parser.add_argument('--resume',        type=str,   default='',          help='恢复训练的 checkpoint 路径')
    parser.add_argument('--no-tensorboard', action='store_true',            help='禁用 TensorBoard')
    parser.add_argument('--export-onnx',   action='store_true',             help='导出 ONNX 格式模型')
    parser.add_argument('--use-tta',       action='store_true',             help='启用测试时增强（Test-Time Augmentation）')

    args = parser.parse_args()
    set_seed(args.seed)
    timestamp = get_timestamp()
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    logs_dir = Path(get_train_logs_dir())
    ckpt_dir = Path(get_checkpoints_dir())
    res_dir  = Path(get_results_dir())

    exp_name = f"{args.model}_cv{args.cv_folds}"
    if args.use_cbam:   exp_name += "_cbam"
    if args.use_mixup:  exp_name += "_mixup"
    if args.use_plantvillage: exp_name += "_pv"
    if args.use_focal_loss: exp_name += "_focal"
    if args.image_size != 224: exp_name += f"_res{args.image_size}"
    if args.use_distill: exp_name += "_distill"
    if args.use_ema: exp_name += "_ema"
    if args.use_randaugment: exp_name += "_randaug"
    if args.use_tta: exp_name += "_tta"
    if args.use_swa: exp_name += "_swa"
    if args.exp_suffix: exp_name += f"_{args.exp_suffix}"
    exp_name += f"_{timestamp}"

    log_file = logs_dir / f"{exp_name}.log"
    log_fh = open(log_file, 'w', encoding='utf-8')

    def log(msg, also_print=True):
        now = datetime.datetime.now().strftime("%H:%M:%S")
        line = f"[{now}] {msg}"
        if also_print:
            print(line, flush=True)
        log_fh.write(line + "\n")
        log_fh.flush()

    writer = None
    if not args.no_tensorboard:
        tb_dir = logs_dir / "tensorboard" / exp_name
        tb_dir.mkdir(parents=True, exist_ok=True)
        writer = SummaryWriter(str(tb_dir))
        log(f"TensorBoard: tensorboard --logdir {tb_dir}")

    log(f"{'='*60}")
    log(f"实验: {exp_name}")
    log(f"设备: {device}")
    log(f"参数: model={args.model}, epochs={args.epochs}, batch={args.batch_size}, lr={args.lr}")
    log(f"      cv_folds={args.cv_folds}, mixup={args.use_mixup}(α={args.mixup_alpha},P={args.mixup_prob})")
    log(f"      cbam={args.use_cbam}, plantvillage={args.use_plantvillage}")
    log(f"      focal_loss={args.use_focal_loss}(γ={args.focal_gamma}), find_lr={args.find_lr}")
    log(f"      warmup={args.warmup_epochs}, ema={args.use_ema}, strong_aug={args.strong_aug}")
    if args.use_randaugment:
        log(f"      randaugment(N={args.randaugment_n},M={args.randaugment_m})")
    if args.use_tta:
        log(f"      tta=flip")
    if args.use_swa:
        log(f"      swa(epochs={args.swa_epochs},lr={args.swa_lr})")
    log(f"      distill={args.use_distill}, temp={args.distill_temp}, alpha={args.distill_alpha}")
    log(f"{'='*60}")

    raw_data = get_raw_data_dir()
    log(f"\n加载数据集: {raw_data}")

    train_paths, train_labels, class_names = load_paths_labels(raw_data / "训练集")
    log(f"  自有训练集: {len(train_paths)} 张, {len(class_names)} 类")

    test_paths, test_labels, _ = load_paths_labels(raw_data / "测试集")
    log(f"  自有测试集: {len(test_paths)} 张")

    if class_names:
        test_class_names = sorted([d.name for d in (raw_data / "测试集").iterdir() if d.is_dir()])
        if test_class_names != class_names:
            log(f"  ⚠️  训练集和测试集类别不一致，使用训练集类别")
            log(f"      训练集: {class_names}")
            log(f"      测试集: {test_class_names}")

    num_classes = len(class_names)
    class_to_idx = {name: i for i, name in enumerate(class_names)}
    idx_to_class = {i: name for name, i in class_to_idx.items()}

    if args.use_plantvillage:
        from backend.shared.paths import get_plantvillage_dir
        pv_dir = get_plantvillage_dir()
        if pv_dir.exists():
            pv_paths, pv_labels = load_plantvillage_for_training(pv_dir, class_names)
            if pv_paths:
                train_paths.extend(pv_paths)
                train_labels.extend(pv_labels)
                log(f"  PlantVillage: +{len(pv_paths)} 张")
            else:
                log(f"  PlantVillage: 未找到匹配数据，跳过")
        else:
            log(f"  PlantVillage 目录不存在: {pv_dir}，跳过")

    log(f"\n  总训练样本: {len(train_paths)}, 类别: {num_classes}")
    for i, cn in enumerate(class_names):
        cnt = train_labels.count(i)
        log(f"    {cn:40s}: {cnt:4d} 张")

    cv_folds = args.cv_folds
    cv_results = []

    test_ds = FruitDiseaseDataset(list(zip(test_paths, test_labels)), get_val_transform(args.image_size))
    test_loader = DataLoader(test_ds, batch_size=args.batch_size, shuffle=False,
                            num_workers=0, pin_memory=True)

    if cv_folds > 1:
        log(f"\n{'='*60}")
        log(f"开始 {cv_folds} 折交叉验证")
        log(f"{'='*60}")

        skf = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=args.seed)

        for fold, (train_idx, val_idx) in enumerate(skf.split(train_paths, train_labels), 1):
            log(f"\n{'─'*40}")
            log(f"Fold {fold}/{cv_folds}")
            log(f"{'─'*40}")

            fold_train_paths = [train_paths[i] for i in train_idx]
            fold_train_labels = [train_labels[i] for i in train_idx]
            fold_val_paths   = [train_paths[i] for i in val_idx]
            fold_val_labels   = [train_labels[i] for i in val_idx]

            class_weights = compute_class_weights(fold_train_labels, num_classes)
            sample_weights = [class_weights[l].item() for l in fold_train_labels]
            sampler = WeightedRandomSampler(sample_weights, num_samples=len(fold_train_labels), replacement=True)

            train_ds = FruitDiseaseDataset(list(zip(fold_train_paths, fold_train_labels)),
                                           get_train_transform(args.image_size, strong_aug=args.strong_aug,
                                                               use_randaugment=args.use_randaugment,
                                                               randaugment_n=args.randaugment_n,
                                                               randaugment_m=args.randaugment_m))
            val_ds   = FruitDiseaseDataset(list(zip(fold_val_paths, fold_val_labels)), get_val_transform(args.image_size))
            collate_fn = make_collate_fn(args.mixup_alpha, args.mixup_prob, args.cutmix_alpha, args.cutmix_prob) if args.use_mixup else None
            train_loader = DataLoader(train_ds, batch_size=args.batch_size, sampler=sampler,
                                      num_workers=0, pin_memory=True, collate_fn=collate_fn)
            val_loader   = DataLoader(val_ds, batch_size=args.batch_size, shuffle=False,
                                      num_workers=0, pin_memory=True)

            model = build_model(args.model, num_classes=num_classes, pretrained=True,
                                use_cbam=args.use_cbam)
            model = model.to(device)
            log(f"  参数量: {sum(p.numel() for p in model.parameters())/1e6:.2f}M")

            criterion = create_criterion(args, class_weights, device,
                                          log_fn=lambda msg: log(f"  {msg}"))
            teacher_model, distill_criterion = create_teacher_and_distill(
                args, num_classes, device, criterion,
                log_fn=lambda msg: log(f"  {msg}")
            )
            optimizer, scheduler, scaler = create_optimizer_and_scheduler(
                args, model, log_fn=lambda msg: log(f"  {msg}")
            )

            if args.find_lr and fold == 1:
                best_lr, _, _ = find_lr(model, train_loader, optimizer, criterion, device)
                args.lr = best_lr
                optimizer.param_groups[0]['lr'] = args.lr
                log(f"  更新学习率为: {args.lr:.6f}")

            fold_ckpt = ckpt_dir / exp_name / f"fold{fold}"
            fold_ckpt.mkdir(parents=True, exist_ok=True)

            if args.resume and fold == 1:
                resume_path = Path(args.resume)
                if resume_path.exists():
                    log(f"  恢复训练: {resume_path}")
                    resume_ckpt = torch.load(resume_path, map_location=device, weights_only=False)
                    model.load_state_dict(resume_ckpt['model_state_dict'])
                    optimizer.load_state_dict(resume_ckpt['optimizer_state_dict'])
                    scheduler.load_state_dict(resume_ckpt['scheduler_state_dict'])
                    if 'scaler_state_dict' in resume_ckpt:
                        scaler.load_state_dict(resume_ckpt['scaler_state_dict'])
                    start_epoch = resume_ckpt.get('epoch', 0) + 1
                    log(f"  从 epoch {start_epoch} 继续训练")

            best_val_acc, best_test_acc, best_epoch, train_history = train_model(
                model, train_loader, val_loader, test_loader, criterion, optimizer, scheduler, scaler,
                args, device, class_names, fold_ckpt,
                lambda msg: log(f"  {msg}", also_print=True),
                writer=writer if writer else None,
                teacher_model=teacher_model,
                distill_criterion=distill_criterion
            )

            log(f"\n  用测试集评估 Fold {fold}...")
            model.load_state_dict(torch.load(fold_ckpt / "best_model.pth")['model_state_dict'])
            if args.use_tta:
                test_loss, test_acc, test_f1, test_preds, test_labels_for_cm, test_probs = validate_with_tta(model, test_loader, criterion, device)
            else:
                test_loss, test_acc, test_f1, test_preds, test_labels_for_cm, test_probs = validate(model, test_loader, criterion, device)
            
            top2_acc = compute_top_k_acc(test_probs, test_labels_for_cm, k=2)
            top3_acc = compute_top_k_acc(test_probs, test_labels_for_cm, k=3)
            
            log(f"  Fold {fold} 测试结果: loss={test_loss:.4f}, acc={test_acc:.2f}%, f1={test_f1:.2f}%")
            log(f"  Fold {fold} Top-2 Acc: {top2_acc:.2f}%, Top-3 Acc: {top3_acc:.2f}%")
            
            train_history['test_loss'] = test_loss
            train_history['test_acc'] = test_acc
            train_history['test_f1'] = test_f1
            train_history['top2_acc'] = top2_acc
            train_history['top3_acc'] = top3_acc
            train_history['best_epoch'] = best_epoch
            train_history['best_val_acc'] = best_val_acc
            
            save_results_json(fold_ckpt / "train_history.json", train_history)
            
            plot_training_curves(train_history, fold_ckpt / "training_curves.png")
            
            cv_results.append({
                'fold': fold, 
                'best_val_acc': round(best_val_acc, 2), 
                'best_epoch': best_epoch,
                'test_acc': round(test_acc, 2),
                'test_f1': round(test_f1, 2),
                'top2_acc': round(top2_acc, 2),
                'top3_acc': round(top3_acc, 2)
            })

        val_accs = [r['best_val_acc'] for r in cv_results]
        test_accs = [r['test_acc'] for r in cv_results]
        test_f1s = [r['test_f1'] for r in cv_results]
        
        mean_val_acc = float(np.mean(val_accs))
        std_val_acc = float(np.std(val_accs))
        mean_test_acc = float(np.mean(test_accs))
        std_test_acc = float(np.std(test_accs))
        mean_test_f1 = float(np.mean(test_f1s))
        std_test_f1 = float(np.std(test_f1s))
        
        log(f"\n{'='*60}")
        log(f"CV {cv_folds}折结果:")
        for r in cv_results:
            log(f"  Fold {r['fold']}: Val Acc={r['best_val_acc']:.2f}%, Test Acc={r['test_acc']:.2f}%, Test F1={r['test_f1']:.2f}%, Top-3={r['top3_acc']:.2f}% @ epoch {r['best_epoch']}")
        log(f"\n  验证集 Acc: {mean_val_acc:.2f}% ± {std_val_acc:.2f}%")
        log(f"  测试集 Acc: {mean_test_acc:.2f}% ± {std_test_acc:.2f}%")
        log(f"  测试集 F1:  {mean_test_f1:.2f}% ± {std_test_f1:.2f}%")
        log(f"{'='*60}")

        save_results_json(res_dir / exp_name / "cv_results.json", {
            'experiment': exp_name, 'model': args.model, 'cv_folds': cv_folds,
            'cv_results': cv_results, 
            'mean_val_acc': mean_val_acc, 'std_val_acc': std_val_acc,
            'mean_test_acc': mean_test_acc, 'std_test_acc': std_test_acc,
            'mean_test_f1': mean_test_f1, 'std_test_f1': std_test_f1,
            'config': vars(args)
        })
    else:
        log("CV 折数 = 1，直接从训练集拆出 80% 训练 / 20% 验证")
        
        tv_paths, val_paths, tv_labels, val_labels = train_test_split(
            train_paths, train_labels, test_size=0.2, random_state=args.seed, stratify=train_labels
        )
        class_weights = compute_class_weights(tv_labels, num_classes)
        sample_weights = [class_weights[l].item() for l in tv_labels]
        sampler = WeightedRandomSampler(sample_weights, num_samples=len(tv_labels), replacement=True)

        train_ds = FruitDiseaseDataset(list(zip(tv_paths, tv_labels)),
                                       get_train_transform(args.image_size, strong_aug=args.strong_aug,
                                                           use_randaugment=args.use_randaugment,
                                                           randaugment_n=args.randaugment_n,
                                                           randaugment_m=args.randaugment_m))
        val_ds   = FruitDiseaseDataset(list(zip(val_paths, val_labels)), get_val_transform(args.image_size))
        collate_fn = make_collate_fn(args.mixup_alpha, args.mixup_prob, args.cutmix_alpha, args.cutmix_prob) if args.use_mixup else None
        train_loader = DataLoader(train_ds, batch_size=args.batch_size, sampler=sampler,
                                  num_workers=0, pin_memory=True, collate_fn=collate_fn)
        val_loader   = DataLoader(val_ds, batch_size=args.batch_size, shuffle=False,
                                  num_workers=0, pin_memory=True)

        model = build_model(args.model, num_classes=num_classes, pretrained=True, use_cbam=args.use_cbam)
        model = model.to(device)
        
        criterion = create_criterion(args, class_weights, device, log_fn=log)
        teacher_model, distill_criterion = create_teacher_and_distill(
            args, num_classes, device, criterion, log_fn=log
        )
        optimizer, scheduler, scaler = create_optimizer_and_scheduler(
            args, model, log_fn=log
        )

        if args.find_lr:
            best_lr, _, _ = find_lr(model, train_loader, optimizer, criterion, device)
            args.lr = best_lr
            optimizer.param_groups[0]['lr'] = args.lr
            log(f"更新学习率为: {args.lr:.6f}")

        simple_ckpt = ckpt_dir / exp_name
        simple_ckpt.mkdir(parents=True, exist_ok=True)

        if args.resume:
            resume_path = Path(args.resume)
            if resume_path.exists():
                log(f"恢复训练: {resume_path}")
                resume_ckpt = torch.load(resume_path, map_location=device, weights_only=False)
                model.load_state_dict(resume_ckpt['model_state_dict'])
                optimizer.load_state_dict(resume_ckpt['optimizer_state_dict'])
                scheduler.load_state_dict(resume_ckpt['scheduler_state_dict'])
                if 'scaler_state_dict' in resume_ckpt:
                    scaler.load_state_dict(resume_ckpt['scaler_state_dict'])
                start_epoch = resume_ckpt.get('epoch', 0) + 1
                log(f"从 epoch {start_epoch} 继续训练")

        best_val_acc, best_test_acc, best_epoch, train_history = train_model(
            model, train_loader, val_loader, test_loader, criterion, optimizer, scheduler, scaler,
            args, device, class_names, simple_ckpt,
            log,
            writer=writer if writer else None,
            teacher_model=teacher_model,
            distill_criterion=distill_criterion
        )

        log(f"\n用测试集评估...")
        model.load_state_dict(torch.load(simple_ckpt / "best_model.pth")['model_state_dict'])
        if args.use_tta:
            test_loss, test_acc, test_f1, test_preds, test_labels_for_cm, test_probs = validate_with_tta(model, test_loader, criterion, device)
        else:
            test_loss, test_acc, test_f1, test_preds, test_labels_for_cm, test_probs = validate(model, test_loader, criterion, device)
        
        top2_acc = compute_top_k_acc(test_probs, test_labels_for_cm, k=2)
        top3_acc = compute_top_k_acc(test_probs, test_labels_for_cm, k=3)
        
        log(f"测试结果: loss={test_loss:.4f}, acc={test_acc:.2f}%, f1={test_f1:.2f}%")
        log(f"Top-2 Acc: {top2_acc:.2f}%, Top-3 Acc: {top3_acc:.2f}%")
        
        train_history['test_loss'] = test_loss
        train_history['test_acc'] = test_acc
        train_history['test_f1'] = test_f1
        train_history['top2_acc'] = top2_acc
        train_history['top3_acc'] = top3_acc
        train_history['best_epoch'] = best_epoch
        train_history['best_val_acc'] = best_val_acc
        
        save_results_json(simple_ckpt / "train_history.json", train_history)
        plot_training_curves(train_history, simple_ckpt / "training_curves.png")

        cv_results = [{
            'fold': 1, 
            'best_val_acc': round(best_val_acc, 2), 
            'best_epoch': best_epoch,
            'test_acc': round(test_acc, 2),
            'test_f1': round(test_f1, 2),
            'top2_acc': round(top2_acc, 2),
            'top3_acc': round(top3_acc, 2)
        }]
        save_results_json(res_dir / exp_name / "cv_results.json", {
            'experiment': exp_name, 'model': args.model, 'cv_folds': 1,
            'cv_results': cv_results, 
            'mean_val_acc': best_val_acc, 'std_val_acc': 0.0,
            'mean_test_acc': test_acc, 'std_test_acc': 0.0,
            'mean_test_f1': test_f1, 'std_test_f1': 0.0,
            'config': vars(args)
        })

    if not args.skip_final_train:
        log(f"\n{'='*60}")
        log("训练最终模型（全部训练数据）")
        log(f"{'='*60}")

        class_weights = compute_class_weights(train_labels, num_classes)
        sample_weights = [class_weights[l].item() for l in train_labels]
        sampler = WeightedRandomSampler(sample_weights, num_samples=len(train_labels), replacement=True)

        final_ds = FruitDiseaseDataset(list(zip(train_paths, train_labels)),
                                       get_train_transform(args.image_size, strong_aug=args.strong_aug,
                                                           use_randaugment=args.use_randaugment,
                                                           randaugment_n=args.randaugment_n,
                                                           randaugment_m=args.randaugment_m))
        collate_fn = make_collate_fn(args.mixup_alpha, args.mixup_prob, args.cutmix_alpha, args.cutmix_prob) if args.use_mixup else None
        final_loader = DataLoader(final_ds, batch_size=args.batch_size, sampler=sampler,
                                   num_workers=0, pin_memory=True, collate_fn=collate_fn)

        val_for_final_ds = FruitDiseaseDataset(list(zip(test_paths, test_labels)), get_val_transform(args.image_size))
        val_for_final_loader = DataLoader(val_for_final_ds, batch_size=args.batch_size, shuffle=False,
                                           num_workers=0, pin_memory=True)

        final_model = build_model(args.model, num_classes=num_classes, pretrained=True, use_cbam=args.use_cbam)
        final_model = final_model.to(device)
        log(f"  参数量: {sum(p.numel() for p in final_model.parameters())/1e6:.2f}M")
        
        criterion = create_criterion(args, class_weights, device,
                                      log_fn=lambda msg: log(f"  {msg}"))
        teacher_model, distill_criterion = create_teacher_and_distill(
            args, num_classes, device, criterion,
            log_fn=lambda msg: log(f"  {msg}")
        )
        optimizer, scheduler, scaler = create_optimizer_and_scheduler(
            args, final_model, log_fn=lambda msg: log(f"  {msg}")
        )

        final_ckpt = ckpt_dir / exp_name / "final"
        final_ckpt.mkdir(parents=True, exist_ok=True)

        best_val_acc_final, best_test_acc_final, best_epoch_final, final_train_history = train_model(
            final_model, final_loader, val_for_final_loader, test_loader, criterion,
            optimizer, scheduler, scaler, args, device, class_names, final_ckpt,
            lambda msg: log(f"  {msg}", also_print=True),
            writer=writer if writer else None,
            teacher_model=teacher_model,
            distill_criterion=distill_criterion
        )

        final_model.load_state_dict(torch.load(final_ckpt / "best_model.pth")['model_state_dict'])

        if args.export_onnx:
            export_model_to_onnx(final_model, device, args.image_size, final_ckpt / "final_model.onnx")
            log(f"  ONNX 模型导出: {final_ckpt / 'final_model.onnx'}")

        log(f"\n{'='*60}")
        log("测试集评估")
        log(f"{'='*60}")

        if args.use_tta:
            test_loss, test_acc, test_f1, preds, trues, probs = validate_with_tta(final_model, test_loader, criterion, device)
        else:
            test_loss, test_acc, test_f1, preds, trues, probs = validate(final_model, test_loader, criterion, device)
        
        top2_acc = compute_top_k_acc(probs, trues, k=2)
        top3_acc = compute_top_k_acc(probs, trues, k=3)

        log(f"  Loss: {test_loss:.4f}")
        log(f"  Acc:  {test_acc:.2f}%")
        log(f"  F1:   {test_f1:.2f}%")
        log(f"  Top-2: {top2_acc:.2f}%")
        log(f"  Top-3: {top3_acc:.2f}%")

        report_str = classification_report(trues, preds, target_names=class_names, digits=4)
        log(f"\n分类报告:\n{report_str}")
        with open(res_dir / exp_name / "classification_report.txt", 'w', encoding='utf-8') as f:
            f.write(report_str)

        cm = confusion_matrix(trues, preds)
        plot_confusion_matrix(cm, class_names, res_dir / exp_name / "confusion_matrix.png")
        np.save(res_dir / exp_name / "confusion_matrix.npy", cm)

        final_train_history['test_loss'] = test_loss
        final_train_history['test_acc'] = test_acc
        final_train_history['test_f1'] = test_f1
        final_train_history['top2_acc'] = top2_acc
        final_train_history['top3_acc'] = top3_acc
        final_train_history['best_epoch'] = best_epoch_final
        final_train_history['best_val_acc'] = best_val_acc_final
        
        save_results_json(final_ckpt / "train_history.json", final_train_history)
        plot_training_curves(final_train_history, final_ckpt / "training_curves.png")

        save_results_json(res_dir / exp_name / "final_results.json", {
            'experiment': exp_name, 'model': args.model,
            'cv_mean_acc': mean_test_acc if cv_folds > 1 else test_acc,
            'test_loss': round(test_loss, 4), 'test_acc': round(test_acc, 2), 'test_f1': round(test_f1, 2),
            'top2_acc': round(top2_acc, 2), 'top3_acc': round(top3_acc, 2),
            'num_classes': num_classes, 'class_mapping': class_to_idx,
            'classification_report': report_str, 'config': vars(args)
        })

        log(f"\n结果保存至: {res_dir / exp_name}")
    else:
        log("\n跳过最终训练 (--skip-final-train)")

    log(f"\n{'='*60}")
    log(f"实验完成: {exp_name}")
    if cv_folds > 1:
        log(f"CV {cv_folds}折 Test Acc: {mean_test_acc:.2f}% ± {std_test_acc:.2f}%")
    if not args.skip_final_train:
        log(f"测试集 Acc: {test_acc:.2f}%, F1: {test_f1:.2f}%")
    log(f"{'='*60}")
    log_fh.close()


if __name__ == "__main__":
    main()
