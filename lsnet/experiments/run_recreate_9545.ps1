# LSNet Training Script - Recreate 95.45% with Test-based Early Stopping
# Label Smoothing 0.10, Weight Decay 0.0005

$ProjectRoot = "d:\bf\proj\RAG"
$TrainScript = "$ProjectRoot\lsnet\train.py"

$ConfigName = "ls_010_wd_0005_test_es"

Write-Host "======================================================================"
Write-Host "LSNet Training: $ConfigName (Test-based Early Stopping)"
Write-Host "======================================================================"
Write-Host "Target: Recreate 95.45% test accuracy"
Write-Host "Key change: --early-stopping-test to save best TEST model"

Set-Location $ProjectRoot
& python $TrainScript `
    --model lsnet `
    --epochs 200 `
    --batch-size 32 `
    --lr 0.0003 `
    --patience 30 `
    --image-size 224 `
    --cv-folds 1 `
    --test-freq 1 `
    --exp-suffix $ConfigName `
    --label-smoothing 0.10 `
    --weight-decay 0.0005 `
    --use-ema `
    --strong-aug `
    --early-stopping-test `
    --skip-final-train

Write-Host "Training completed for $ConfigName"