#!/bin/bash
#SBATCH --job-name=bdw_gguf_quant
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
source $HOME/bdw-llm/venv_p2/bin/activate
echo "node      : $(hostname)"
echo "date      : $(date -Is)"
df -h /home | tail -1
echo

F16=$HOME/bdw-llm/merged/bdw-7b-sft-f16.gguf
Q4=$HOME/bdw-llm/merged/bdw-7b-sft-Q4_K_M.gguf
QZ=$HOME/bdw-llm/llama_cpp/build/bin/llama-quantize

cd $HOME/bdw-llm/llama_cpp || exit 1

if [ ! -s "$F16" ]; then
  echo "=== convert hf -> gguf f16 ==="
  python convert_hf_to_gguf.py $HOME/bdw-llm/merged/bdw-7b-sft \
    --outfile "$F16" --outtype f16 || { echo "RESULT: P2_GGUF_CONVERT_FAIL"; exit 1; }
fi
ls -lh "$F16"

if [ ! -s "$Q4" ]; then
  echo "=== quantize f16 -> Q4_K_M ==="
  $QZ "$F16" "$Q4" Q4_K_M || { echo "RESULT: P2_GGUF_QUANTIZE_FAIL"; exit 1; }
fi
ls -lh "$Q4"

echo "=== md5 ==="
md5sum "$F16" "$Q4" | tee $HOME/bdw-llm/merged/gguf_md5.txt

if [ -s "$F16" ] && [ -s "$Q4" ]; then
  echo "RESULT: P2_GGUF_QUANT_OK f16_bytes=$(stat -c%s "$F16") q4_bytes=$(stat -c%s "$Q4")"
else
  echo "RESULT: P2_GGUF_QUANT_FAIL"
  exit 1
fi
