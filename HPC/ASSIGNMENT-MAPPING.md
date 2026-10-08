# Assignment Mapping

Maps solution programs to their originating assignment documents across the C, C++, Linux, Python, and HPC courses.

## C++ (05-CPP-PROGRAMMING/08-ASSIGNMENTS)

| Day | Assignment document | Solution programs |
|-----|---------------------|-------------------|
| DAY-01 | `DAY-01/Amit_Kumar_C++_Class_Assignment.docx` | `01_circle_area.cpp`, `02_employee_oop.cpp`, `03_temperature_oop.cpp`, `04_login_password.cpp`, `05_speaker_volume.cpp` |
| DAY-01 | `DAY-01/Amit_Kumar_C++_Namespace_Assignment.docx` (+ `_alt`) | `01a_circle_square_collision_namespace.cpp`, `01b_india_usa_currency_namespace.cpp`, `05a_company_hr_nested_namespace.cpp` |
| DAY-02 | `DAY-02/Amit_Kumar_C++_Day1_Assignment.docx` (+ `_alt`, `_variant1`) | code in `04-OOP` (deep-copy classes) |
| DAY-04 | `DAY-04/Amit_Kumar_C++_Lambda_Assignment.docx` | `01_lambda_basic.cpp` … `07_lambda_capture_by_ref.cpp` |
| root   | `Amit_Kumar_C++_Lambda_Assignment.docx` | (duplicate of DAY-04 sheet) |

## C (04-C-AND-DS/18-ASSIGNMENTS)

| Day / topic | Assignment document | Solution programs |
|-------------|---------------------|-------------------|
| DAY-02 | `DAY-02/*.pdf` | `03-CONDITIONALS/` `q01..q09` + `04-ASSIGNMENTS/` |
| DAY-03 | `DAY-03/*.pdf` `*.docx` | arrays/`05-ASSIGNMENTS/` `q01..q10` |
| DAY-04 | `DAY-04/*.pdf` `*.docx` | `06-ARRAYS/02-2D-ARRAYS/`, `03-3D-ARRAYS/` |
| DAY-05 | `DAY-05/*.pdf` `*.docx` | functions + pointers `q01..q20` |
| DAY-06 | `DAY-06/*` | `08-FUNCTIONS/` |
| DAY-07 | `DAY-07/*`, `DAY7-POINTERS/` | `10-POINTERS/` |
| FUNCTION | `FUNCTION/*.docx` | `08-FUNCTIONS/04-ASSIGNMENTS/` |
| STRING | `STRING/*.docx` | `07-STRINGS/03-PRACTICE/` |
| MULTI-DIM-ARRAY | `MULTI-DIM-ARRAY/*.docx` `*.pdf` | `06-ARRAYS/02-2D-ARRAYS/` |
| root | `Amit_Kumar_C_Assignment.docx`(+ `.pdf`) | (full course submission) |

## Linux (02-LINUX-AND-OS)

| Source | Solution programs |
|--------|-------------------|
| `COURSE-MATERIAL/Comprehensive_Linux_OS_Lab_Assignment.docx` | `SOLUTIONS/q01…q28` (files, users, processes, scripts) |
| `COURSE-MATERIAL/Linux-Hands-On Practice Assignment.docx` | `SOLUTIONS/q29…q58` (vi/nano, paging/segmentation) |
| `COURSE-MATERIAL/Linux_OS_Question_Paper.pdf` | OS memory notes in `COURSE-MATERIAL/q53_q58_paging_segmentation_notes.sh` |

## Python (06-PYTHON-PROGRAMMING/01-PYTHON-BASICS)

| Assignment | Location |
|------------|----------|
| `Python_Assignment1.ipynb` (Colab) | `04-ASSIGNMENTS/python_assignment1.ipynb` |

## HPC (07-HPC-AND-ITS-ARCHITECTURE)

Assignment sheet → where its solution(s) live. All paths relative to `07-HPC-AND-ITS-ARCHITECTURE/`.

| Assignment sheet | Solution(s) |
|------------------|-------------|
| `COURSE-MATERIAL/ASSIGNMENTS/assignment1_parallel_statements.pdf` | `COURSE-MATERIAL/ASSIGNMENTS/SOLUTIONS/assignment1_parallel_statements_solutions.md` — 16 exercises (source skips Ex 6), each marked parallel/not with its RAW/WAR/WAW dependence |
| `COURSE-MATERIAL/ASSIGNMENTS/assignment_day2_hpc_arch.pdf` (13 concept questions) | `COURSE-MATERIAL/ASSIGNMENTS/hpc_architecture_conclusion.docx` — already answers all 13 plus Rmax/Rpeak, InfiniBand, RDMA, GPU, workload characterization |
| `COURSE-MATERIAL/ASSIGNMENTS/cloud_computing_assignment.docx` (IaaS/PaaS/SaaS) | same document — self-contained writing assignment |
| `COURSE-MATERIAL/ASSIGNMENTS/openmp_mpi_hybrid_problems.pdf` §1 OpenMP (5) | `01-OPENMP-PARALLELISM/04-ASSIGNMENTS/openmp_{array_sum_stats,matmul_scheduling,prime_sieve,task_producer_consumer,task_mergesort}.cpp` |
| `openmp_mpi_hybrid_problems.pdf` §2 MPI (5) | `04-MPI-COMMUNICATION/04-ASSIGNMENTS/mpi_{scatter_reduce_sum,matvec_gather,ring_sendrecv,trapezoidal,sample_sort}.cpp` |
| `openmp_mpi_hybrid_problems.pdf` §3 Hybrid MPI+OpenMP (5) | `04-MPI-COMMUNICATION/04-ASSIGNMENTS/hybrid/hybrid_{saxpy,matmul,stencil_2d,monte_carlo_pi,kmeans}.cpp` |
| `COURSE-MATERIAL/ASSIGNMENTS/python_parallel_day1_assignment.pdf` (10) | `05-PYTHON-PARALLELISM/04-ASSIGNMENTS/day-01/ex01..ex10_*.py` |
| `python_parallel_day2_assignment.pdf` (5) | `05-PYTHON-PARALLELISM/04-ASSIGNMENTS/day-02/ex01..ex05_*.py` |
| `python_parallel_day3_assignment.pdf` (5) | `05-PYTHON-PARALLELISM/04-ASSIGNMENTS/day-03/ex01..ex05_*.py` |
| `python_parallel_day4_assignment.pdf` (4) | `05-PYTHON-PARALLELISM/04-ASSIGNMENTS/day-04/` (scoop/Pyro4/rpyc/celery files — see its `README.md`) |
| `python_parallel_day5_assignment.pdf` (5) | `05-PYTHON-PARALLELISM/04-ASSIGNMENTS/day-05/ex01..ex05_*.py` + `README.md` (GPU or CPU-fallback) |

**Verification status** — every program below was **executed on the CDAC Delhi PARAM Rudra
cluster** (`paramrudra.cdacdelhi.in`, gcc 12.3.0 + Open MPI 4.1.5, Python 3.11.4):

- OpenMP `§1` — 6 programs (incl. the pre-existing `matrix_mult_openmp`) compile with
  `-Wall -Wextra -O2` at **0 warnings**, run with `OMP_NUM_THREADS=4` and print `PASS`.
  SLURM job **31155**, `~/hpc/results/`.
- MPI `§2` (5) + Hybrid `§3` (5) — compile with `mpicxx -Wall -Wextra -O2` at **0 warnings**
  and run under `mpirun` (4 ranks for `§2`, 2 ranks × 2 threads for `§3`), all printing `PASS`.
  SLURM job **31155**. Note `mpicc` does **not** link `libstdc++` — these C++ sources must be
  built with `mpicxx`/`mpic++`. The blocking Send/Recv deadlock demo in `mpi_ring_sendrecv`
  is gated behind `--deadlock` so the default run cannot hang.
- `hybrid_kmeans` — first run failed its invariant check (job 31155): the assignment counter
  summed the **already-global** `gcnt` and then reduced again, reporting `n × P` points
  (200000 instead of 100000). Fixed to sum the local `cnt[]`; job **31156** now prints
  `all points assigned exactly once: yes / RESULT: PASS`.
- Python — all **31** scripts run green (job **31157**): day-1 (10), day-2 (5), day-3 (5, of
  which `ex01/ex02` run under `mpirun -np 4` with `mpi4py` 4.1.2), day-4 (scoop, Pyro4, RPyC
  and the full Celery pipeline against a live Redis broker + worker), day-5 (5).
  `day-05` GPU sheets take their CPU architectural-simulation path — `pycuda`/`pyopencl` are
  absent and no CUDA device is visible; `numba` 0.68.0 is installed.

## Notes

- Assignment `.docx`/`.pdf` marked `_alt`/`_variant`/`(duplicate)` are near-identical revisions kept to preserve source; the primary sheet is the un-suffixed file.
- Redundant examples are quarantined under `99-REFERENCES/REVIEW/`.