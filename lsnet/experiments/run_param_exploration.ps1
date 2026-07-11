# LSNet Training Script - Parameter Exploration
# Testing different label smoothing and weight decay values

$ProjectRoot = "d:\bf\proj\RAG"
$TrainScript = "$ProjectRoot\lsnet\train.py"

# Configuration list to test
$Configs = @(
    @{Name="ls_010_wd_0005"; LabelSmoothing=0.10; WeightDecay=0.0005},
    @{Name="ls_010_wd_001"; LabelSmoothing=0.10; WeightDecay=0.001},
    @{Name="ls_005_wd_001"; LabelSmoothing=0.05; WeightDecay=0.001},
    @{Name="ls_020_wd_001"; LabelSmoothing=0.20; WeightDecay=0.001},
    @{Name="ls_015_wd_0005"; LabelSmoothing=0.15; WeightDecay=0.0005},
    @{Name="ls_015_wd_002"; LabelSmoothing=0.15; WeightDecay=0.002}
)

foreach ($Config in $Configs) {
    $ConfigName = $Config.Name
    $LabelSmoothing = $Config.LabelSmoothing
    $WeightDecay = $Config.WeightDecay
    
    Write-Host "======================================================================"
    Write-Host "LSNet Training: $ConfigName"
    Write-Host "Label Smoothing: $LabelSmoothing | Weight Decay: $WeightDecay"
    Write-Host "======================================================================"
    
    Set-Location $ProjectRoot
    & python $TrainScript `
        --model lsnet `
        --epochs 200 `
        --batch-size 32 `
        --lr 0.0003 `
        --patience 30 `
        --image-size 224 `
        --cv-folds 1 `
        --skip-final-train `
        --test-freq 5 `
        --exp-suffix $ConfigName `
        --label-smoothing $LabelSmoothing `
        --weight-decay $WeightDecay `
        --use-ema `
        --strong-aug `
        --early-stopping-test
    
    Write-Host "Training completed for $ConfigName"
    Write-Host ""
}