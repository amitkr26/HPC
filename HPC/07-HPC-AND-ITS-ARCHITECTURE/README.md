# Module 07 - Introduction to HPC & Its Architecture

- **Duration:** 48 hrs / 6 Days
- **Faculty:** Anuja Sridhar (PE STG)
- **Schedule:** 10/09/2026 - 17/09/2026
- **Holidays:** 12/09 - 13/09/2026 (Weekend)

## Folder layout

```
07-HPC-AND-ITS-ARCHITECTURE/
├── README.md                  <- you are here
├── COURSE-MATERIAL/           <- course supplies
│   ├── REFERENCE/             <-   lecture PDFs + PPTs (intro, admin, day 1/2)
│   └── ASSIGNMENTS/           <-   assignment sheets + submitted solutions
├── 01-OPENMP-PARALLELISM/
│   ├── 02-EXAMPLES/           <- thread IDs, num_threads/if, work-sharing, firstprivate/private
│   └── 04-ASSIGNMENTS/        <- matrix multiply (OpenMP + serial timing)
├── 02-PTHREADS/
│   ├── 01-CONCEPTS/           <- API reference image + ps thread command
│   └── 02-EXAMPLES/           <- POSIX pthread worker demo
└── 03-STD-THREAD/
    ├── 01-CONCEPTS/           <- API reference image + ps thread command
    └── 02-EXAMPLES/           <- std::thread worker demo
```

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