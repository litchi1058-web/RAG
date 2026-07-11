cd d:\bf\proj\RAG\lsnet

python train.py ^
    --model lsnet ^
    --data-dir data/custom ^
    --image-size 256 ^
    --batch-size 32 ^
    --epochs 150 ^
    --lr 0.0001 ^
    --weight-decay 0.0005 ^
    --label-smoothing 0.10 ^
    --use-ema ^
    --strong-aug ^
    --early-stopping-test ^
    --test-freq 10 ^
    --patience 20 ^
    --seed 42 ^
    --use-distill ^
    --teacher-ckpt "d:\bf\proj\RAG\vgg-data\xiaorong_shiyan\results\Full\best_model.pth" ^
    --distill-temp 4.0 ^
    --distill-alpha 0.5