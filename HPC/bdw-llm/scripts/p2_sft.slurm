#!/bin/bash
#SBATCH --job-name=bdw_p2sft
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
#SBATCH --signal=B:USR1@60
source $HOME/bdw-llm/venv_p2/bin/activate
echo "node      : $(hostname)"
echo "date      : $(date -Is)"
echo "which py  : $(which python)"
echo "CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-unset}"
echo "signal    : B:USR1@60 (python checkpoints atomically and exits at T-60s)"
echo
ls -lh ${P2_SFT_DATA:-$HOME/bdw-llm/data/bdw_sft.jsonl}
echo
nvidia-smi -L
echo
trap '[ -n "${PY_PID:-}" ] && kill -USR1 $PY_PID 2>/dev/null' USR1
trap '[ -n "${PY_PID:-}" ] && kill -TERM $PY_PID 2>/dev/null' TERM
python $HOME/bdw-llm/src/p2_sft.py &
PY_PID=$!
# bash's `wait` returns 128+signo the moment a trap fires even if python is
# still alive -- keep waiting until the child really exits, or Slurm would tear
# the job down while python is mid-save (job 32654 lesson).
rc=0
while kill -0 "$PY_PID" 2>/dev/null; do
    wait "$PY_PID"
    rc=$?
done
echo "sft rc=$rc"
exit $rc
