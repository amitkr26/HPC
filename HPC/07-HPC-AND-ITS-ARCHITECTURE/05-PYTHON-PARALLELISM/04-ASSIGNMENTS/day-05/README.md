# Day 05 — GPU Programming with Python (Assignment Solutions)

Five standalone scripts from `python_parallel_day5_assignment.pdf`.
Run each with `python <file>`; every script prints clear verification output and
exits non-zero on failure.

| File | Topic | Needs | CPU-only run |
|---|---|---|---|
| `ex01_pycuda_vector_scale.py` | `cuda.mem_alloc`, `memcpy_htod/dtoh`, `SourceModule` kernel | **pycuda + NVIDIA GPU** | Yes — architectural-simulation fallback reproduces the 5-step data flow (host alloc → device alloc → H2D → kernel-equivalent compute → D2H) in NumPy |
| `ex02_pycuda_matrix_transpose.py` | 2D grid/thread transpose kernel (16×16 blocks) | **pycuda + NVIDIA GPU** | Yes — block-by-block 2D grid walk in NumPy with the literal kernel index math + boundary check |
| `ex03_gpuarray_expressions.py` | `gpuarray.to_gpu`, operator math, `ElementwiseKernel` (ReLU) | **pycuda + NVIDIA GPU** | Yes — NumPy simulation of transfer/compute/read-back, verified against NumPy reference |
| `ex04_numba_shared_memory.py` | `@cuda.jit`, `cuda.grid`, `cuda.shared.array`, `cuda.syncthreads` | **numba + CUDA device** | Yes — thread-accurate simulation (shared-tile load → barrier → neighbour reads), verified against an independent reference |
| `ex05_pyopencl_runner.py` | Platform/device discovery, OpenCL C kernel build & enqueue | **pyopencl + an OpenCL runtime/driver** | Yes — discovery runs (reports missing pyopencl clearly), then a NumPy simulation of the buffer → enqueue → read-back pipeline |

## Fallback behaviour

* GPU imports are always guarded (`try/except`); when the library or device is
  missing the script prints `MODE: CPU architectural simulation`, performs the
  same data flow in NumPy, and verifies results against a CPU reference.
* On a machine with the library + GPU installed, the real device path runs
  instead — no code changes needed.

## Environment notes

* Verified with numpy 2.x; `pycuda`, `numba`, `pyopencl` were **not** installed
  on the authoring machine (no NVIDIA GPU), so all five ran via their fallback
  paths (ex05 also exercises its discovery step, which reports the missing
  library gracefully).
* Kernel explanations from the spec's *Hints & Guidelines* live in each
  script's module docstring rather than inline comments.
* `ex04`: the spec's kernel only writes lanes with `0 < t_id < 255` and
  `g_id < n-1`, so block-edge lanes (t_id 0 and 255) and the final sample stay
  `0.0`. The verification honours those exact conditions.
