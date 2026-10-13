# Module 09 - Advanced Programming (HPC)

- **Duration:** 72 hrs / 9 Days
- **Faculty:** Anuja Sridhar (PE STG)
- **Schedule:** 25/09/2026 - 08/10/2026
- **Holidays:** 26/09 - 27/09/2026 (Weekend), 02/10/2026 (Mahatma Gandhi Birthday), 03/10 - 04/10/2026 (Weekend)

Content to be added as the course progresses.

## Folder layout

```
09-ADVANCED-PROGRAMMING-HPC/
├── README.md                  <- you are here
├── PROFILING/                 <- performance-analysis tools session
│   ├── README.md              <-   build/run/profile instructions
│   ├── test1.c                <-   busy-loop sample (main → func1 → new_func1 → func2)
│   ├── test2.c                <-   definition of new_func1()
│   └── setupscript.sh         <-   TAU 2.33.1 + binutils/gprofng PATH setup
└── DEBUGGING/                 <- GDB debugger session (09/10/2026)
    ├── README.md              <-   compile flags, GDB walkthroughs, verified behaviour
    ├── COURSE-MATERIAL/       <-   31-slide debugger deck + 2-page command sheet
    └── LAB-CODES/             <-   the five labs (hello, crash, factorial[_fix],
                                   matrix_multiply[_race], vector_add.cu)
```

## Profiling

```bash
cd PROFILING
gcc -O0 -g test1.c test2.c -o test   # -O0 keeps the spin loops from being optimized away
./test
source ./setupscript.sh              # tau_exec + gprofng on PATH
gprofng display text ./test
tau_exec ./test
```

The original drop included a 27 MB Intel VTune result bundle; the profiler
databases were left out of git — only the reproducible source is kept (see
`PROFILING/README.md`).

## Debugging

```bash
cd DEBUGGING/LAB-CODES
gcc -g -O0 -fopenmp matrix_multiply.c -o matrix_multiply
OMP_NUM_THREADS=4 gdb ./matrix_multiply
(gdb) info threads
(gdb) thread apply all bt
```

Always build with `-g -O0`: `-g` emits the DWARF symbols GDB needs and `-O0`
keeps variables live so `print` works. See `DEBUGGING/README.md` for the
per-lab walkthroughs and the verified outputs.