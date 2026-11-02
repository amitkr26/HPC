#!/bin/bash
#SBATCH --job-name=bdw_p4sft
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
# P4.4 -- LoRA SFT for one router domain on the shipped P2.5 model
# (merged/bdw-7b-sft). Rebuilds the domain SFT dataset deterministically
# (P4.2) before training, then runs the slice protocol (auto-resume,
# --signal=B:USR1@60 finalize, mid-slice wall checkpoint).
# Resubmittable: operates like the P2.3 chained slices.
source $HOME/bdw-llm/venv_p2/bin/activate
DOMAIN=${DOMAIN:?export DOMAIN=math|vlsi|embedded|cs|aiml before sbatch}
export P4_DOMAIN=$DOMAIN
echo "node      : $(hostname)"
echo "date      : $(date -Is)"
echo "which py  : $(which python)"
echo "domain    : $DOMAIN"
echo "signal    : B:USR1@60 (python checkpoints atomically and exits at T-60s)"
echo
echo "base model (P2.5 merge, offline):"
ls -lh "$HOME/bdw-llm/merged/bdw-7b-sft/config.json" \
      "$HOME/bdw-llm/merged/bdw-7b-sft/chat_template.jinja"
echo
echo "teacher QA (P4.1) + previous dataset state:"
wc -l "$HOME/bdw-llm/data/p4/qa/${DOMAIN}_qa.jsonl" 2>/dev/null \
  || echo "  (no QA rows yet)"
wc -l "$HOME/bdw-llm/data/p4/sft/${DOMAIN}_sft.jsonl" 2>/dev/null \
  || echo "  (no SFT dataset yet)"
echo
echo "resume state (run dir):"
ls -d "$HOME/bdw-llm/sft_runs/p4_${DOMAIN}"/checkpoint-* 2>/dev/null \
  || echo "  (fresh run)"
echo
nvidia-smi -L
echo
echo "=== P4.2 deterministic dataset build ==="
python "$HOME/bdw-llm/src/p4_build_sft.py" --domain "$DOMAIN" || {
  echo "P4.2 build failed -> not training"; exit 1; }
echo
trap '[ -n "${PY_PID:-}" ] && kill -USR1 $PY_PID 2>/dev/null' USR1
trap '[ -n "${PY_PID:-}" ] && kill -TERM $PY_PID 2>/dev/null' TERM
python "$HOME/bdw-llm/src/p4_lora_sft.py" &
PY_PID=$!
# bash's `wait` returns 128+signo the moment a trap fires even if python is
# still alive -- keep waiting until the child really exits, or Slurm would
# tear the job down while python is mid-save (job 32654 lesson).
rc=0
while kill -0 "$PY_PID" 2>/dev/null; do
    wait "$PY_PID"
    rc=$?
done
echo "p4 sft rc=$rc"
exit $rc
