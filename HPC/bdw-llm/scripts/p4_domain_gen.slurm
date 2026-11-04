#!/bin/bash
#SBATCH --job-name=bdw_p4gen
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
# P4.1 -- teacher Q&A generation for one router domain.
# export DOMAIN=math|embedded|cs|aiml|vlsi  (vlsi already has Stage O.3a
# grounded QA -- its context reuse is validated on login; no GPU job needed).
# Resubmittable any number of times: the QA writer resumes by chunk id.
source $HOME/bdw-llm/venv_p2/bin/activate
DOMAIN=${DOMAIN:?export DOMAIN=math|embedded|cs|aiml|vlsi before sbatch}
export P4_DOMAIN=$DOMAIN
echo "node      : $(hostname)"
echo "date      : $(date -Is)"
echo "which py  : $(which python)"
echo "domain    : $DOMAIN"
echo "CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-unset}"
echo
echo "context payload (P4.0):"
ls -lh "$HOME/bdw-llm/data/raw/p4_${DOMAIN}_contexts.json" 2>/dev/null \
  || ls -lh "$HOME/bdw-llm/data/raw/vlsi_wikipedia.json" 2>/dev/null \
  || echo "  MISSING -- run src/p4_fetch_domain_contexts.py on the login node"
echo
echo "teacher (offline):"
ls -lh "$HOME/bdw-llm/teacher_model_7b/model.safetensors.index.json"
echo
echo "resume state (P4 qa rows):"
wc -l "$HOME/bdw-llm/data/p4/qa/${DOMAIN}_qa.jsonl" 2>/dev/null \
  || echo "  (none yet -- full run)"
echo
nvidia-smi -L
echo
exec python "$HOME/bdw-llm/src/p4_gen_domain_qa.py" --domain "$DOMAIN" "$@"
