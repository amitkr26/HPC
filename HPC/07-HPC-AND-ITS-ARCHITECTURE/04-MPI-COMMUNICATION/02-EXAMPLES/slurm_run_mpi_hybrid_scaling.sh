#!/bin/bash
#SBATCH --job-name=hybrid_mvm_scaling
#SBATCH --output=hybrid_mvm_scaling_%j.out
#SBATCH --error=hybrid_mvm_scaling_%j.err
#SBATCH --partition=cpu
#SBATCH --nodes=2
#SBATCH --ntasks-per-node=1       # 1 MPI rank per node
#SBATCH --cpus-per-task=1         # pin 1 core/task; --exclusive gives the whole node anyway
#SBATCH --time=02:00:00
#SBATCH --exclusive               # grab the whole node
#SBATCH --hint=nomultithread      # use only physical cores

set -u

export OMPI_MCA_btl="^openib"

module load openmpi-4.1.6

SRC="mpi_omp_hybrid_mvm.cpp"
BIN="mpi_omp_hybrid_mvm"

NCORES=$(nproc)

echo "=== Environment ==="
echo "Job ID      : ${SLURM_JOB_ID:-local}"
echo "Node list   : ${SLURM_JOB_NODELIST:-$(hostname)}"
echo "Tasks/node  : ${SLURM_NTASKS_PER_NODE:-1}"
echo "Cores/node  : ${NCORES}"
echo "OMP threads : ${OMP_NUM_THREADS:-auto -> uses all ${NCORES} cores}"
echo

echo "=== Available memory per node ==="
for h in $(scontrol show hostname ${SLURM_JOB_NODELIST:-$(hostname)}); do
    echo -n "$h : "
    srun --nodelist=${h} --nodes=1 --ntasks=1 --overlap bash -c 'free -g | sed -n 2p'
done
echo

# ----------------------------------------------------------------
# Compute the largest n this 2-node config can hold jointly.
#
# Each of the 2 ranks (1 per node) stores:
#     local_A : n x (n/2) doubles = 4*n^2  bytes
#     local_y : n doubles         =   8*n  bytes
#     local_x : (n/2) doubles     =   4*n  bytes
# So per-node memory ~ 4*n^2. We target 80% of the free RAM.
# ----------------------------------------------------------------
FREEMEM_B=$(free -b | awk '/^Mem:/{print $7}')
MAX_N=$(awk -v m="$FREEMEM_B" 'BEGIN { n = int(sqrt((m * 0.8) / 4)); printf "%d", n }')
MAX_N=$(( (MAX_N / 2) * 2 ))          # must be divisible by 2 (rank count)

echo "=== Compile ==="
mpic++ -O3 -fopenmp ${SRC} -o ${BIN} || { echo "compilation failed"; exit 1; }
echo "built ${BIN}"
echo

# ----------------------------------------------------------------
# Sweep increasing n (each divisible by 2) up to the memory bound.
# Override with: SWEEP_N="20000 40000 80000 ..." ./script.slurm
# ----------------------------------------------------------------
if [ -n "${SWEEP_N:-}" ]; then
    read -ra SIZES <<< "$SWEEP_N"
else
    STEP=$(( (MAX_N / 12 / 2) * 2 ))
    [ "$STEP" -lt 5000 ] && STEP=5000
    SIZES=()
    for (( n = STEP; n <= MAX_N; n += STEP )); do
        SIZES+=("$n")
    done
    # guarantee the memory-bound size is included
    [ "${SIZES[-1]}" != "$MAX_N" ] && SIZES+=("$MAX_N")
fi

echo "Sweep sizes (n): ${SIZES[*]}"
echo "Scanning sizes; max is tuned to leave headroom under node RAM (n_max=$MAX_N)."
echo

RESULTS=( )

for n in "${SIZES[@]}"; do
    echo -n "n=$n ... "
    OUT=$(mpirun -np 2 ./${BIN} "$n" 2>&1)

    if echo "$OUT" | grep -q "not divisible\|terminated by signal\|Killed\|out of memory"; then
        echo "FAILED (out of memory / crash) - stopping sweep"
        echo "$OUT" | tail -5
        echo
        break
    fi

    MS=$(echo "$OUT"   | sed -n 's/.*runtime(ms): *//p')
    PASS=$(echo "$OUT" | sed -n 's/Correctness: *\(PASS\|FAIL\).*/\1/p')
    echo "runtime=$MS ms  correctness=$PASS"
    RESULTS+=( "$n $MS $PASS" )
done

echo
echo "=============================================================="
echo "SCALING RESULTS  (2 CPU nodes, 1 rank/node, ${NCORES} OMP threads/node)"
echo "=============================================================="
printf "%-14s %-16s %-10s\n" "Matrix size n" "Runtime (ms)" "Correct"
printf "%-14s %-16s %-10s\n" "------------" "------------" "-------"
for r in "${RESULTS[@]}"; do
    read -r n ms pass <<< "$r"
    printf "%-14s %-16.1f %-10s\n" "$n" "$ms" "$pass"
done
echo "--------------------------------------------------------------"
LAST_N=$(echo "${RESULTS[-1]}" | awk '{print $1}')
echo "Joint max load sustained by the 2 nodes: n = ${LAST_N}"
echo "  (per-node memory ~ 4*n^2 bytes, sized to 80% of free RAM)"
echo