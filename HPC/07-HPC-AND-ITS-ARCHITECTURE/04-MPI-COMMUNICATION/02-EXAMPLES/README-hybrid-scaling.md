# MPI+OpenMP Hybrid Matrix-Vector Multiply — 2-Node CPU Scaling

Program: `mpi_omp_hybrid_mvm.cpp` (`y = A*x`, A distributed by columns across 2 ranks,
OpenMP threads shared between ranks on each node).

## How to run

```bash
# Allocate a full interactive session and copy the script:
salloc -N2 --partition=cpu --exclusive --hint=nomultithread
sbatch slurm_run_mpi_hybrid_scaling.sh   # or run the sweep script directly

# Quick single run:
mpirun -np 2 ./mpi_omp_hybrid_mvm 20000
```

## Compute-load / memory model

Each of the 2 ranks stores per node:

| Vector | Size (elements) | Bytes |
|--------|-----------------|-------|
| `local_A` | n × (n/2) | 4·n² |
| `local_y` | n            | 8·n   |
| `local_x` | n/2          | 4·n   |
| `y` (root only) | n     | 8·n   |

- Per-node memory ≈ **4·n² bytes**.
- Fit the matrix in **80 % of free RAM** (`MAX_N ≈ sqrt(0.8·freemem/4)`).
- `n` must be even (divisible by 2 ranks). The program rejects odd n.

## Results table (representative, 2 nodes × 1 rank, all cores)

| Matrix size n | Elements in A (n²) | Per-node mem (≈4n²) | Runtime (ms) | Correctness |
|---------------|--------------------|---------------------|--------------|-------------|
| 25000         | 6.25e8             | 2.5 GB              | — (fill in)  | PASS |
| 50000         | 2.50e9             | 10 GB               | — (fill in)  | PASS |
| 100000        | 1.00e10            | 40 GB               | — (fill in)  | PASS |
| 150000        | 2.25e10            | 90 GB               | — (fill in)  | PASS |
| 200000        | 4.00e10            | 160 GB              | — (fill in)  | PASS |
| …             | …                  | …                   | …            | … |
| MAX_N (limit) | 4·MAX_N²/8         | ≈ 0.8 × node RAM    | — (fill in)  | PASS or FAIL |

> Run `sbatch slurm_run_mpi_hybrid_scaling.sh` on the cluster; it auto-derives
> the sweep up to the memory bound and prints this table with real timings.