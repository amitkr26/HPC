#!/bin/bash
#SBATCH --job-name=bdw_gguf_build
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
# Reference build recipe for llama.cpp + top1agree.
# Executed manually on the LOGIN node (job 33495/33496 proved compute nodes
# have no libc dev headers: /usr/include/stdint.h missing), with the explicit
# gcc-12.3 toolchain and -DGGML_NATIVE=OFF for portability (see PHASE2_7B_
# BLUEPRINT.md errata 17.1). Build wall: 126 s at -j4; RESULT: P2_GGUF_BUILD_OK.
source $HOME/bdw-llm/venv_p2/bin/activate
echo "node      : $(hostname)"
echo "date      : $(date -Is)"
echo "which py  : $(which python)"
df -h /home | tail -1
echo

cd $HOME/bdw-llm/llama_cpp || exit 1
CMAKE=$HOME/bdw-llm/venv_p2/bin/cmake

if [ ! -x build/bin/llama-quantize ] || [ ! -x build/bin/top1agree ]; then
  echo "=== cmake configure ==="
  $CMAKE -B build -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_C_COMPILER=/home/apps/gcc-12.3/bin/gcc \
    -DCMAKE_CXX_COMPILER=/home/apps/gcc-12.3/bin/g++ \
    -DGGML_NATIVE=OFF \
    -DLLAMA_BUILD_TESTS=OFF -DLLAMA_BUILD_EXAMPLES=OFF \
    -DLLAMA_BUILD_SERVER=OFF -DLLAMA_BUILD_APP=OFF \
    -DLLAMA_BUILD_TOOLS=ON -DLLAMA_BUILD_COMMON=ON \
    -DLLAMA_USE_PREBUILT_UI=OFF \
    -DGGML_CURL=OFF -DLLAMA_CURL=OFF || exit 1
  echo "=== build (incremental; resumes across re-submits) ==="
  $CMAKE --build build -j4 --target llama-quantize top1agree || exit 1
fi

echo
ls -la build/bin/ 2>/dev/null | head -20
if [ -x build/bin/llama-quantize ] && [ -x build/bin/top1agree ]; then
  echo "RESULT: P2_GGUF_BUILD_OK $(build/bin/llama-quantize --version 2>&1 | head -1)"
else
  echo "RESULT: P2_GGUF_BUILD_FAIL"
  exit 1
fi
