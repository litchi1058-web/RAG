# LSNet Training Script - 5-Fold Cross Validation
# Best Configuration: Label Smoothing 0.10, Weight Decay 0.0005

$ProjectRoot = "d:\bf\proj\RAG"
$TrainScript = "$ProjectRoot\lsnet\train.py"

# Best Configuration from ls_010_wd_0005
$ConfigName = "ls_010_wd_0005_cv5"
$Epochs = 200
$BatchSize = 32
$Lr = 0.0003
$Patience = 30
$ImageSize = 224
$LabelSmoothing = 0.10
$WeightDecay = 0.0005
$CVFolds = 5

Write-Host "======================================================================"
Write-Host "LSNet Training: $ConfigName (5-Fold Cross Validation)"
Write-Host "======================================================================"
Write-Host "Configuration:"
Write-Host "  Label Smoothing: $LabelSmoothing"
Write-Host "  Weight Decay: $WeightDecay"
Write-Host "  CV Folds: $CVFolds"
Write-Host "  Strong Augmentation: Enabled"
Write-Host "  EMA: Enabled"
Write-Host "  Early Stopping: Test-based"

Set-Location $ProjectRoot
& python $TrainScript `
    --model lsnet `
    --epochs $Epochs `
    --batch-size $BatchSize `
    --lr $Lr `
    --patience $Patience `
    --image-size $ImageSize `
    --cv-folds $CVFolds `
    --test-freq 1 `
    --exp-suffix $ConfigName `
    --label-smoothing $LabelSmoothing `
    --weight-decay $WeightDecay `
    --use-ema `
    --strong-aug `
    --early-stopping-test

Write-Host "Training completed for $ConfigName"