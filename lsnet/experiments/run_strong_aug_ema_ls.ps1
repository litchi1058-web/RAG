# LSNet Training Script - Strong Augmentation + Regularization
# Target: Test accuracy >= 94%

$ProjectRoot = "d:\bf\proj\RAG"
$TrainScript = "$ProjectRoot\lsnet\train.py"

# Configuration: Strong Aug + Label Smoothing + EMA + High Weight Decay
$ConfigName = "strong_aug_ema_ls"
$Epochs = 200
$BatchSize = 32
$Lr = 0.0003
$Patience = 30
$ImageSize = 224
$LabelSmoothing = 0.15
$WeightDecay = 0.001
$GradClip = 1.0

Write-Host "======================================================================"
Write-Host "LSNet Training: $ConfigName"
Write-Host "======================================================================"
Write-Host "Configuration: Strong Augmentation + Label Smoothing + EMA"

# Run training
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
    --test-freq 5 `
    --exp-suffix $ConfigName `
    --label-smoothing $LabelSmoothing `
    --weight-decay $WeightDecay `
    --grad-clip $GradClip `
    --use-ema `
    --strong-aug

Write-Host "Training completed for $ConfigName"