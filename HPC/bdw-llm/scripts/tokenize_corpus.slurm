#!/bin/bash
#SBATCH -J bdw_e_tok
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
echo "node   : $(hostname)"
echo "python : $(which python)"
echo "date   : $(date -Is)"
echo
python $HOME/bdw-llm/src/tokenize_corpus.py
echo
echo "TOKENIZE_STAGE_DONE rc=$?"
