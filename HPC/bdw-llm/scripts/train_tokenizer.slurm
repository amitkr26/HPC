#!/bin/bash
#SBATCH -J bdw_d_tok
#SBATCH -p standard
#SBATCH -N 1
#SBATCH -n 1
#SBATCH --cpus-per-task=4
#SBATCH -t 00:14:00
#SBATCH --account=tutor
#SBATCH --qos=training
#SBATCH -o %x-%j.out
#SBATCH -e %x-%j.err
source $HOME/bdw-llm/env.sh
echo "node     : $(hostname)"
echo "python   : $(which python)"
echo "cpus     : $(nproc)"
echo "date     : $(date -Is)"
echo
python $HOME/bdw-llm/src/train_tokenizer.py
echo
echo "TOK_STAGE_DONE rc=$?"
