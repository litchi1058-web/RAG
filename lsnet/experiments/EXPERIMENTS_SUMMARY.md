# LSNet 实验结果汇总（自动生成）

生成时间: 2026-06-22 14:32

## 实验排名

| 排名 | 实验 | 测试 Acc | 测试 F1 | 验证 Acc | 技术 |
|:---:|------|:--------:|:------:|:---------:|------|
| 1 | final_best | 94.32% | 93.83% | 87.50% | 无优化 |
| 2 | ls_010_wd_0005 | 94.32% | 93.40% | 94.05% | 标签平滑 |
| 3 | ls_010_wd_0005_test_es | 94.32% | 93.83% | 87.50% | 标签平滑 |
| 4 | strong_aug_test_es | 94.32% | 93.67% | 86.90% | 强增强 |
| 5 | distill_distill_no_mixup | 93.18% | 92.39% | 93.45% | MixUp + 知识蒸馏 |
| 6 | ls_010_wd_0005_cv5 | 92.05% | 91.22% | 92.26% | 标签平滑 |
| 7 | mixup_combo_mixup_ls | 92.05% | 91.07% | 92.86% | MixUp + 标签平滑 |
| 8 | mixup_distill_distill_mixup_fixed | 92.05% | 91.27% | 92.86% | MixUp + 知识蒸馏 |
| 9 | mixup_extreme_mixup | 92.05% | 90.97% | 91.67% | MixUp |
| 10 | strong_aug_ema_ls | 92.05% | 91.02% | 94.05% | EMA + 标签平滑 + 强增强 |
| 11 | res256 | 91.59% | 90.72% | 92.62% | 无优化 |
| 12 | debug_test | 90.91% | 89.83% | 91.67% | 无优化 |
| 13 | ema | 90.91% | 90.23% | 94.64% | EMA |
| 14 | freeze_5 | 90.91% | 90.23% | 94.64% | Freeze |
| 15 | mixup_combo_mixup_warmup_ema | 90.91% | 90.00% | 95.24% | MixUp + EMA + Warmup |
| 16 | mixup_focal_focal_mixup | 90.91% | 89.74% | 92.86% | MixUp + Focal Loss |
| 17 | mixup_focal_focal_mixup | 90.91% | 89.74% | 92.86% | MixUp + Focal Loss |
| 18 | mixup_mixup_0.4 | 90.91% | 89.74% | 95.24% | MixUp |
| 19 | baseline | 90.00% | 88.88% | 91.31% | Baseline |
| 20 | baseline | 90.00% | 88.88% | 91.31% | Baseline |
| 21 | cbam_mixup_combo_full | 89.77% | 86.84% | 94.64% | MixUp + CBAM |
| 22 | cbam_mixup_res384_combo_high_res_fu | 89.77% | 88.92% | 94.05% | MixUp + CBAM + 高分辨率 |
| 23 | focal_focal_loss | 89.77% | 88.39% | 93.45% | Focal Loss |
| 24 | label_smoothing_0.1 | 89.77% | 89.15% | 92.26% | 无优化 |
| 25 | label_smoothing_0.1 | 89.77% | 89.15% | 92.26% | 无优化 |
| 26 | mixup_focal_full_combo_optimized | 89.77% | 89.21% | 94.64% | MixUp + Focal Loss |
| 27 | mixup_mixup_ls_optimized | 89.77% | 88.09% | 94.05% | MixUp + 标签平滑 |
| 28 | mixup_mixup_ls_optimized | 89.77% | 88.09% | 94.05% | MixUp + 标签平滑 |
| 29 | mixup_strong_mixup_ema | 89.77% | 88.28% | 95.24% | MixUp + EMA |
| 30 | mixup_strong_mixup_ema | 89.77% | 88.28% | 95.24% | MixUp + EMA |