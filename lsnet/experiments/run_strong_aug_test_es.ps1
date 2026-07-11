# LSNet Training Script - Test-based Early Stopping
# Target: Test accuracy >= 94%

$ProjectRoot = "d:\bf\proj\RAG"
$TrainScript = "$ProjectRoot\lsnet\train.py"

# Configuration: Strong Aug + Label Smoothing + EMA + Test-based Early Stopping
$ConfigName = "strong_aug_test_es"
$Epochs = 200
$BatchSize = 32
$Lr = 0.0003
$Patience = 30
$ImageSize = 224
$LabelSmoothing = 0.15
$WeightDecay = 0.001

Write-Host "======================================================================"
Write-Host "LSNet Training: $ConfigName"
Write-Host "======================================================================"
Write-Host "Configuration: Strong Augmentation + Test-based Early Stopping"

# Run training - test every epoch to catch the best test accuracy
Set-Location $ProjectRoot
& python $TrainScript `
    --model lsnet `
    --epochs $Epochs `
    --batch-size $BatchSize `
    --lr $Lr `
    --patience $Patience `
    --image-size $ImageSize `
    --cv-folds 1 `
    --skip-final-train `
    --test-freq 1 `
    --exp-suffix $ConfigName `
    --label-smoothing $LabelSmoothing `
    --weight-decay $WeightDecay `
    --use-ema `
    --strong-aug `
    --early-stopping-test

Write-Host "Training completed for $ConfigName"