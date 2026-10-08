# Module 07 - Introduction to HPC & Its Architecture

- **Duration:** 48 hrs / 6 Days
- **Faculty:** Anuja Sridhar (PE STG)
- **Schedule:** 10/09/2026 - 17/09/2026
- **Holidays:** 12/09 - 13/09/2026 (Weekend)
- **Lecture recordings:** 15/09 - 25/09/2026 in Google Drive — see [`COURSE-MATERIAL/RECORDINGS.md`](COURSE-MATERIAL/RECORDINGS.md)

## Folder layout

```
07-HPC-AND-ITS-ARCHITECTURE/
├── README.md                  <- you are here
├── COURSE-MATERIAL/           <- course supplies
│   ├── RECORDINGS.md          <-   index of Drive lecture videos + Gemini session notes
│   ├── REFERENCE/             <-   lecture PDFs + PPTs (intro, admin, parallel programming deck, day 1/2/4/5 sessions, cluster setup)
│   └── ASSIGNMENTS/           <-   assignment sheets + submitted solutions
│       └── SOLUTIONS/         <-   written answers (Assignment 1 data-dependence sheet)
├── 01-OPENMP-PARALLELISM/
│   ├── 02-EXAMPLES/           <- thread IDs, num_threads/if, work-sharing, firstprivate/private, sections, single, critical, atomic, barrier, reduction, threadprivate/copyprivate
│   └── 04-ASSIGNMENTS/        <- matrix multiply + openmp problems sheet §1 (array stats, matmul scheduling, sieve, task producer/consumer, task mergesort)
├── 02-PTHREADS/
│   ├── 01-CONCEPTS/           <- API reference image + ps thread command
│   └── 02-EXAMPLES/           <- POSIX pthread worker demo
├── 03-STD-THREAD/
│   ├── 01-CONCEPTS/           <- API reference image + ps thread command
│   └── 02-EXAMPLES/           <- std::thread worker demo
├── 04-MPI-COMMUNICATION/
│   ├── 02-EXAMPLES/           <- P2P sync/async + collectives + MPI/OpenMP hybrid mvm + SLURM run script
│   └── 04-ASSIGNMENTS/        <- problems sheet §2 MPI (scatter, matvec, ring, trapezoid, sample sort)
│       └── hybrid/            <-   §3 hybrid MPI+OpenMP (saxpy, matmul, 2D stencil, Monte Carlo, k-means)
└── 05-PYTHON-PARALLELISM/     <- Python parallel day-1..5 (faculty Anuja)
    ├── 02-EXAMPLES/           <- day-1: JSON/pickle serialization, threads vs processes + GIL, Pool/speedup/Amdahl
    │   ├── day-02/            <- day-2: Lock/RLock/Semaphore, Condition/Event/Barrier/Queue, process lifecycle, Pool/Queue/Pipe
    │   │   └── classroom-examples/   <- day-2 threading/multiprocessing classroom scripts (ex01-ex07 + vinutils)
    │   ├── day-04/            <- day-4: distributed Python (Celery/RabbitMQ, Pyro4 + rpyc RPC, SCOOP, Docker)
    │   │   └── classroom-examples/   <- ex01 Celery+RabbitMQ, ex02 Pyro4, ex03 rpyc, ex04 Docker/Scoop
    │   └── day-05/            <- day-5: GPU — PyCUDA, Numba CUDA, PyOpenCL (each with a SLURM .sh)
    │       └── classroom-examples/   <- ex01-ex04 (.py + .sh pairs, GPU partition)
    ├── 03-PRACTICE/           <- day-1: t01-t07 JSON, pickle round-trip + security, threads, locks
    │   └── day-03/            <- day-3: mpi4py availability/collective, ThreadPool vs ProcessPool (factorial)
    │       └── classroom-examples/   <- day-3 ex01-ex06 (python-concurrent execution, MPI in Python)
    └── 04-ASSIGNMENTS/        <- solutions to the day-1..5 lab sheets
        ├── day-01/            <- 10 exercises (JSON, pickle, word count, threads, pipeline, GIL, race, memory, speedup, toolkit)
        ├── day-02/            <-  5 (RLock, semaphore pool, barrier, IPC pipeline, async pool callbacks)
        ├── day-03/            <-  5 (MPI ring, MPI pi, futures, asyncio, asyncio+executor)
        ├── day-04/            <-  4 (SCOOP, Pyro4, rpyc, Celery) + README
        └── day-05/            <-  5 (PyCUDA x3, Numba, OpenCL) + README (CPU fallbacks)
```

## Python parallel (day-1..5)

All `.py` in `05-PYTHON-PARALLELISM` run standalone:

```bash
python 05-PYTHON-PARALLELISM/02-EXAMPLES/day-02/01_thread_sync_primitives.py
python 05-PYTHON-PARALLELISM/03-PRACTICE/day-03/classroom-examples/ex05.py   # needs mpi4py/numpy for ex02-ex04
```

Day-3 `ex02-ex04` need `mpi4py` (+ `numpy`); day-2 `ex03` needs `requests`. Install per the `requirements.txt` in each folder. Course material for the Python track lives in `COURSE-MATERIAL` (day-1..5 assignment PDFs, session slides, SLURM guide).

**Day-4 (distributed):** `ex01` needs `celery`/`kombu` plus a running RabbitMQ (see `ex01/run.sh`, `ex01/rabbitmq.conf`);
`ex02` needs `Pyro4` and `pyro-ns`; `ex03` needs `rpyc`; `ex04` is a Docker image for `scoop`.

**Day-5 (GPU):** needs `pycuda` / `numba` / `pyopencl` and a CUDA-capable node. Each `ex0N.sh` is a SLURM
batch script for the `gpu` partition (`sbatch ex01.sh`) — it loads `cuda/12.3`, activates `hpc_env`, then runs
the matching `.py`. Cluster bootstrap: `COURSE-MATERIAL/REFERENCE/hpc_cluster_setup.pdf` (Conda + MPI).

## Assignment solutions

Every sheet in `COURSE-MATERIAL/ASSIGNMENTS/` now has a solution — see
[`../ASSIGNMENT-MAPPING.md`](../ASSIGNMENT-MAPPING.md) for the full sheet → solution table.

| Sheet | Where |
|-------|-------|
| Assignment 1 — data dependence (16 exercises) | `COURSE-MATERIAL/ASSIGNMENTS/SOLUTIONS/assignment1_parallel_statements_solutions.md` |
| Day-2 HPC architecture (13 questions) | already answered by `COURSE-MATERIAL/ASSIGNMENTS/hpc_architecture_conclusion.docx` |
| OpenMP / MPI / Hybrid problems (15 programs) | `01-OPENMP-PARALLELISM/04-ASSIGNMENTS/`, `04-MPI-COMMUNICATION/04-ASSIGNMENTS/` (+ `hybrid/`) |
| Python lab sheets day-1..5 (29 scripts) | `05-PYTHON-PARALLELISM/04-ASSIGNMENTS/day-01` … `day-05` |

```bash
# OpenMP section — builds and runs anywhere with g++
g++ -std=c++17 -fopenmp -Wall -Wextra -O2 01-OPENMP-PARALLELISM/04-ASSIGNMENTS/openmp_prime_sieve.cpp -o sieve
./sieve

# MPI + hybrid sections — need an MPI toolchain on the cluster; each file header documents its mpirun line
mpic++ -std=c++17 -fopenmp -O2 04-MPI-COMMUNICATION/04-ASSIGNMENTS/mpi_sample_sort.cpp -o sample_sort
mpirun -np 4 ./sample_sort 1000000
```

All 15 assignment programs **plus** the pre-existing `matrix_mult_openmp` were executed on the
CDAC PARAM Rudra cluster (SLURM jobs 31155/31156) — each build is warning-free and each run
prints `PASS`. Build MPI and hybrid sources with `mpicxx`, not `mpicc`: `mpicc` does not link
`libstdc++` and fails with `undefined reference to operator new`. Python day-1…day-5 (31
scripts) all pass under job 31157: `mpi4py` covers day-3 `ex01/ex02`; `scoop`, `Pyro4`, `rpyc`,
`celery` and `numba` are installed in `~/hpc/venv`, and the day-4 Celery pipeline runs against
a live Redis broker + worker. The day-5 GPU sheets take their CPU architectural-simulation
fallback (`pycuda`/`pyopencl` are absent and no CUDA device is visible).

## Compilation (OpenMP C++)

```bash
g++ program.cpp -o program.exe -fopenmp
program.exe
```

## Compilation (pthread / std::thread)

```bash
g++ program.cpp -o program.exe -pthread    # pthread_worker_demo.cpp
g++ program.cpp -o program.exe -pthread    # std_thread_worker_demo.cpp (+ /std:c++17 on MSVC, -std=c++11 on Linux)
program.exe
```

Both thread programs print from the main thread plus two workers for 10 seconds while the OS `sleep()` runs — use the `threads_ps_cmd.txt` command (`ps -t pts/0 -m -o pid,tid,nlwp,cmd`) to observe the thread count on Linux.

## Compilation (MPI)

Requires an MPI implementation (e.g. OpenMPI). On Linux with `mpic++`:

```bash
mpic++ 02_p2p_async_nonblocking.cpp -o 02_p2p_async
mpirun -np 2 ./02_p2p_async        # run the .cpp example with 2 ranks
```

On a SLURM cluster, submit `04-MPI-COMMUNICATION/02-EXAMPLES/slurm_run_mpi_demo.sh` with `sbatch`. The P2P demos need exactly 2 ranks; collective demos scale to any rank count (hard-coded buffers support up to 4).