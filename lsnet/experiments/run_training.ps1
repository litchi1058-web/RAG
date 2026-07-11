# LSNet Training Script for Parameter Search
# Target: Test accuracy >= 94%

param(
    [string]$ConfigName = "mixup_ls_optimized",
    [int]$Epochs = 150,
    [int]$BatchSize = 32,
    [double]$Lr = 0.0005,
    [int]$Patience = 25,
    [int]$ImageSize = 224,
    [double]$MixupAlpha = 0.4,
    [double]$MixupProb = 0.8,
    [double]$LabelSmoothing = 0.05,
    [int]$FreezeEpochs = 3,
    [int]$WarmupEpochs = 3,
    [bool]$UseEma = $true,
    [bool]$UseMixup = $true
)

$ProjectRoot = "d:\bf\proj\RAG"
$TrainScript = "$ProjectRoot\lsnet\train.py"

# Build arguments
$ArgsList = @(
    "--model", "lsnet",
    "--epochs", $Epochs,
    "--batch-size", $BatchSize,
    "--lr", $Lr,
    "--patience", $Patience,
    "--image-size", $ImageSize,
    "--cv-folds", "1",
    "--skip-final-train",
    "--test-freq", "5",
    "--exp-suffix", $ConfigName
)

if ($UseMixup) {
    $ArgsList += @("--use-mixup", "--mixup-alpha", $MixupAlpha, "--mixup-prob", $MixupProb)
}

if ($LabelSmoothing > 0) {
    $ArgsList += @("--label-smoothing", $LabelSmoothing)
}

if ($UseEma) {
    $ArgsList += "--use-ema"
}

if ($FreezeEpochs > 0) {
    $ArgsList += @("--freeze-epochs", $FreezeEpochs)
}

if ($WarmupEpochs > 0) {
    $ArgsList += @("--warmup-epochs", $WarmupEpochs)
}

Write-Host "======================================================================"
Write-Host "LSNet Training: $ConfigName"
Write-Host "======================================================================"
Write-Host "Arguments: $($ArgsList -join ' ')"

# Run training
Set-Location $ProjectRoot
& python $TrainScript $ArgsList

Write-Host "Training completed for $ConfigName"