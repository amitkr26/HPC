#!/bin/bash
#SBATCH --job-name=bdw_distill
#SBATCH --partition=gpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gpus=1
#SBATCH --cpus-per-task=4
#SBATCH --time=00:15:00
#SBATCH --account=tutor
#SBATCH --qos=training
#SBATCH --output=%x-%j.out
#SBATCH --error=%x-%j.err
source $HOME/bdw-llm/env.sh
echo "node      : $(hostname)"
echo "date      : $(date -Is)"
echo "which py  : $(which python)"
echo "CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-unset}"
echo
echo "distilled shards (7B teacher, Stage N.3a):"
ls -lh $HOME/bdw-llm/data/distilled_tokens/shards/
echo
echo "base checkpoint (Stage L best):"
ls -lh $HOME/bdw-llm/checkpoints_ft/step_0003000.pt
echo
echo "existing checkpoints_distilled_v2/ (resume if present):"
ls -lh $HOME/bdw-llm/checkpoints_distilled_v2/ 2>/dev/null || echo "  (none yet)"
echo
nvidia-smi -L
echo

ARGS="--shard-dir $HOME/bdw-llm/data/distilled_tokens/shards"
ARGS="$ARGS --ckpt-dir $HOME/bdw-llm/checkpoints_distilled_v2"
ARGS="$ARGS --base-ckpt $HOME/bdw-llm/checkpoints_ft/step_0003000.pt"
ARGS="$ARGS --stage-tag N4"

echo "=== baseline: Stage L checkpoint scored on the distilled held-out shard ==="
python $HOME/bdw-llm/src/finetune.py $ARGS \
  --eval-only --eval-ckpt $HOME/bdw-llm/checkpoints_ft/step_0003000.pt
echo "baseline rc=$?"
echo
echo "=== distillation fine-tune (N.4 v2 data, resumes from checkpoints_distilled_v2/) ==="
exec python $HOME/bdw-llm/src/finetune.py $ARGS \
  --total-steps 200 \
  --warmup-steps 20 \
  --lr 1.5e-5 \
  --min-lr 1.5e-6 \
  --batch-size 8 \
  --eval-interval 25 \
  --ckpt-interval-s 300 \
  --val-shards 1 \
  --keep-ckpt 3 \
  --log-interval 10
