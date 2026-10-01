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
│   ├── REFERENCE/             <-   lecture PDFs + PPTs (intro, admin, day 1/2)
│   └── ASSIGNMENTS/           <-   assignment sheets + submitted solutions
├── 01-OPENMP-PARALLELISM/
│   ├── 02-EXAMPLES/           <- thread IDs, num_threads/if, work-sharing, firstprivate/private, sections, single, critical, atomic, barrier, reduction, threadprivate/copyprivate
│   └── 04-ASSIGNMENTS/        <- matrix multiply (OpenMP + serial timing)
├── 02-PTHREADS/
│   ├── 01-CONCEPTS/           <- API reference image + ps thread command
│   └── 02-EXAMPLES/           <- POSIX pthread worker demo
├── 03-STD-THREAD/
│   ├── 01-CONCEPTS/           <- API reference image + ps thread command
│   └── 02-EXAMPLES/           <- std::thread worker demo
├── 04-MPI-COMMUNICATION/
│   ├── 02-EXAMPLES/           <- P2P sync/async + collectives + MPI/OpenMP hybrid mvm + SLURM run script
│   └── (hybrid problems sheet in COURSE-MATERIAL/ASSIGNMENTS)
└── 05-PYTHON-PARALLELISM/     <- Python parallel day-1/2/3 (faculty Anuja)
    ├── 02-EXAMPLES/           <- day-1: JSON/pickle serialization, threads vs processes + GIL, Pool/speedup/Amdahl
    │   └── day-02/            <- day-2: Lock/RLock/Semaphore, Condition/Event/Barrier/Queue, process lifecycle, Pool/Queue/Pipe
    │       └── classroom-examples/   <- day-2 threading/multiprocessing classroom scripts (ex01-ex07 + vinutils)
    └── 03-PRACTICE/           <- day-1: t01-t07 JSON, pickle round-trip + security, threads, locks
        └── day-03/            <- day-3: mpi4py availability/collective, ThreadPool vs ProcessPool (factorial)
            └── classroom-examples/   <- day-3 ex01-ex06 (python-concurrent execution, MPI in Python)
```

## Python parallel (day-1/2/3)

All `.py` in `05-PYTHON-PARALLELISM` run standalone:

```bash
python 05-PYTHON-PARALLELISM/02-EXAMPLES/day-02/01_thread_sync_primitives.py
python 05-PYTHON-PARALLELISM/03-PRACTICE/day-03/classroom-examples/ex05.py   # needs mpi4py/numpy for ex02-ex04
```

Day-3 `ex02-ex04` need `mpi4py` (+ `numpy`); day-2 `ex03` needs `requests`. Install per the `requirements.txt` in each folder. Course material for the Python track lives in `COURSE-MATERIAL` (day-1/2/3 assignment PDFs, session slides, SLURM guide).

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