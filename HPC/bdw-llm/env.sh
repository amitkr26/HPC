# Source this at the top of every BDW job script / shell session:
#     source $HOME/bdw-llm/env.sh
# It selects the project venv even if .bashrc activated ~/hpc/venv.
export BDW_ROOT="$HOME/bdw-llm"
source "$BDW_ROOT/venv/bin/activate"
