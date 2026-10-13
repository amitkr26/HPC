# Debugging with GDB (module 09)

Materials from the *Advanced Programming – HPC* **Debugger** session
(Monojyotsna Koch, 09/10/2026): a lecture deck, a command sheet and the five
lab programs used in the session.

## Files

| File | Lab | What it demonstrates |
|------|-----|----------------------|
| `COURSE-MATERIAL/gdb_debugger_slides.pdf` | — | 31-slide deck: what debugging is, GDB fundamentals, intermediate GDB, OpenMP threads, GPU debugging (`cuda-gdb` / `rocgdb`), 5-question quiz with answers |
| `COURSE-MATERIAL/gdb_debugging_command_sheet.pdf` | — | 2-page cheat sheet: compile flags, start/exit, breakpoints, stepping, inspecting data, threads/OpenMP, CUDA-GDB, ROCgdb, common signals |
| `LAB-CODES/hello.cpp` | 1 | Basic commands: `break`, `run`, `next`, `print`, `set var`, `watch`, `info locals` |
| `LAB-CODES/crash.c` | 2 | Segmentation fault through a NULL pointer — `backtrace`, `frame N`, `print`, `watch` |
| `LAB-CODES/factorial.c` | 3 | Watchpoints + conditional breakpoints; `int` overflows at 13! |
| `LAB-CODES/factorial_fix.c` | 3 | Same program with `long long` (correct up to 20!) |
| `LAB-CODES/matrix_multiply.c` | 4a | Correct OpenMP matmul — `sum` is private (declared inside the loop) |
| `LAB-CODES/matrix_multiply_race.c` | 4b | OpenMP data race — `sum` is declared outside the parallel loop, so it is shared |
| `LAB-CODES/vector_add.cu` | 5 | CUDA-GDB demo: missing `if (idx < n)` bounds check in the kernel |

## Compile for debugging

`-g` writes the DWARF symbols GDB needs; `-O0` keeps variables live so `print`
shows real values instead of `<value optimized out>`.

```bash
cd LAB-CODES
gcc -g -O0        -o hello        hello.cpp     # or g++ for C++
gcc -g -O0        -o crash        crash.c
gcc -g -O0        -o factorial    factorial.c
gcc -g -O0 -fopenmp -o matrix_multiply matrix_multiply.c
nvcc -g -G -arch=sm_80 -o vector_add vector_add.cu   # sm_80 = A100; see note below
```

## Walkthroughs

**Lab 1 — `hello.cpp`** (after the two additions `j` is 10 and `k` is 20)

```text
$ gdb ./hello
(gdb) break main
(gdb) run
(gdb) next
(gdb) print j
(gdb) print k
(gdb) set j = 5
(gdb) info breakpoints
(gdb) watch j
(gdb) quit
```

**Lab 2 — `crash.c`** (a NULL pointer reaches `crash()`, which writes through it)

```text
(gdb) run
Program received signal SIGSEGV, Segmentation fault.
(gdb) backtrace
(gdb) frame 1
(gdb) print j          # j is 0x0
(gdb) watch j
```

**Lab 3 — `factorial.c`** (`13! = 6227020800` exceeds `INT_MAX`)

```text
(gdb) break factorial if n == 13
(gdb) run
(gdb) watch result
(gdb) continue
(gdb) print result
```

**Lab 4a/4b — OpenMP matmul**

```bash
OMP_NUM_THREADS=4 gdb ./matrix_multiply
```

```text
(gdb) info threads
(gdb) thread 2
(gdb) info locals      # private values of the same names in each thread
(gdb) thread apply all bt
```

**Lab 5 — `vector_add.cu`** (verified on PARAM Rudra's `gpu` partition, NVIDIA A100 80GB)

The kernel is missing its `if (idx < n)` guard: with `n = 1000` and 256 threads
per block the grid rounds up to 4 blocks (1024 threads), so threads 1000–1023
write past the end of `c`.

```bash
module load cuda/12.3
nvcc -g -G -arch=sm_80 -o vector_add vector_add.cu
compute-sanitizer --tool memcheck ./vector_add
```

```text
./vector_add                          -> c[10]=30.0 c[999]=2997.0   exit 0   <- silent!
compute-sanitizer --tool memcheck      -> ERROR SUMMARY: 28 errors
```

The program does **not** crash on a plain run — the corruption is invisible
until `compute-sanitizer` reports it. Adding `if (idx >= n) return;` right
after the index calculation takes the report to **0 errors** with the same
output.

> **Build on the login node, run on the GPU node.** The `gpu` partition's
> `/usr/include` is stripped down to three entries, so `nvcc` on `rdgpu01`/`rdgpu02`
> fails with `fatal error: features.h: No such file or directory` even though
> `glibc-devel` is installed. Compile on `login02` (where the headers are intact),
> then run the binary on a GPU node — `/home` is shared NFS, so the executable
> is already there. Submit with `#SBATCH -p gpu --gpus=1`.

## Verified behaviour

All six native programs build warning-free with `gcc -g -O0` (GCC 13.2) and
behave exactly as the deck describes:

| Program | Result |
|---------|--------|
| `hello.cpp` | builds and runs; `j` = 10, `k` = 20 before `set j = 5` |
| `crash.c` | builds; aborts with an access violation (`0xC0000005`) — the NULL-pointer write |
| `factorial.c` | `n=13` prints `1932053504` — the documented `int` overflow |
| `factorial_fix.c` | `n=13` prints `6227020800` |
| `matrix_multiply.c` | runs; `C[0][0]=140`, `C[7][7]=-252` |
| `matrix_multiply_race.c` | `OMP_NUM_THREADS=4` → **14774 mismatches** vs the serial reference, so the race reproduces reliably |

`vector_add.cu` is not built on Windows — it needs `nvcc` plus an NVIDIA GPU.
It **was** verified on the cluster: built with CUDA 12.3 on `login02` and run on
`rdgpu01` (A100 80GB), where the missing bounds check produced 28 memcheck
errors and the fixed version produced 0.

## Quick tips from the sheet

- Enter repeats the last command; Tab completes.
- `No symbol "i" in current context` means the wrong frame or scope — use
  `info locals` or `frame N`.
- A breakpoint inside a hot loop stops every pass — use `delete`, `disable` or
  a condition.
- Races depend on timing: a program that passes once is not proven correct.
