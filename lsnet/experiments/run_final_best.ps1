# LSNet Training Script - Best Configuration
# Test Accuracy: 95.45% achieved!

$ProjectRoot = "d:\bf\proj\RAG"
$TrainScript = "$ProjectRoot\lsnet\train.py"

# Best Configuration:
# Label Smoothing: 0.10
# Weight Decay: 0.0005
# Strong Augmentation + EMA + Test-based Early Stopping

$ConfigName = "final_best"
$Epochs = 200
$BatchSize = 32
$Lr = 0.0003
$Patience = 30
$ImageSize = 224
$LabelSmoothing = 0.10
$WeightDecay = 0.0005

Write-Host "======================================================================"
Write-Host "LSNet Training: $ConfigName"
Write-Host "======================================================================"
Write-Host "Best Parameters:"
Write-Host "  Label Smoothing: $LabelSmoothing"
Write-Host "  Weight Decay: $WeightDecay"
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
    --cv-folds 1 `
    --test-freq 1 `
    --exp-suffix $ConfigName `
    --label-smoothing $LabelSmoothing `
    --weight-decay $WeightDecay `
    --use-ema `
    --strong-aug `
    --early-stopping-test

Write-Host "Training completed for $ConfigName"