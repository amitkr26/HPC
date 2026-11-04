"""Exercise 4: Pure Python GPU Kernels with Numba (@cuda.jit) & Shared Memory.

Implements a 3-point moving average  y[i] = (x[i-1] + x[i] + x[i+1]) / 3  as a
Numba CUDA kernel:

    * cuda.shared.array(shape=(256,), dtype=np.float32) allocates an on-chip
      SRAM tile (much lower latency than global VRAM) for the thread block.
    * Each thread loads its global element x[g_id] into shared_tile[t_id]
      (global -> shared).
    * cuda.syncthreads() is a block-level barrier: every thread of the block
      must reach it before any thread continues, so the tile is complete.
    * The stencil then reads only the fast shared tile (shared memory is
      private to a block; threads of other blocks cannot see it).
    * Launch configuration: threads_per_block = 256,
      blocks_per_grid = ceil(n / 256).

Boundary semantics kept faithful to the spec's kernel: only threads with
0 < t_id < 255 and g_id < n - 1 write output, so block-edge lanes (t_id 0 and
255 of every block) and the very last sample keep the initial 0.0.

Without numba (or a CUDA device) the script runs a thread-accurate NumPy
simulation of the kernel - shared tile load, barrier, neighbour reads - and
verifies it against an independently computed reference.
"""

import numpy as np

N = 4096
THREADS_PER_BLOCK = 256
BLOCKS_PER_GRID = (N + THREADS_PER_BLOCK - 1) // THREADS_PER_BLOCK

KERNEL_SRC = """
@cuda.jit
def moving_average_kernel(input_data, output_data):
    shared_tile = cuda.shared.array(shape=(256,), dtype=np.float32)
    t_id = cuda.threadIdx.x
    g_id = cuda.grid(1)
    if g_id < input_data.size:
        shared_tile[t_id] = input_data[g_id]
    cuda.syncthreads()
    if 0 < t_id < 255 and g_id < input_data.size - 1:
        output_data[g_id] = (shared_tile[t_id - 1] + shared_tile[t_id] +
                             shared_tile[t_id + 1]) / 3.0
"""


def prepare_signal():
    """Host signal: 4096 random float32 samples (seeded) plus zeroed output."""
    rng = np.random.default_rng(11)
    x = rng.standard_normal(N).astype(np.float32)
    y = np.zeros(N, dtype=np.float32)
    return x, y


def run_on_gpu(x, y):
    """Real Numba CUDA path. Returns False if numba or a CUDA device is absent."""
    try:
        from numba import cuda
        if not cuda.is_available():
            print("[GPU] numba is installed but no CUDA device is available")
            return False
    except Exception as exc:
        print(f"[GPU] Numba unavailable -> {type(exc).__name__}: {exc}")
        return False

    ns = {"cuda": cuda, "np": np}
    exec(KERNEL_SRC, ns)
    kernel = ns["moving_average_kernel"]
    d_in = cuda.to_device(x)
    d_out = cuda.to_device(y)
    print("[LAUNCH] kernel[{}, {}] - shared tile of 256 float32 per block".format(
        BLOCKS_PER_GRID, THREADS_PER_BLOCK))
    kernel[BLOCKS_PER_GRID, THREADS_PER_BLOCK](d_in, d_out)
    d_out.copy_to_host(y)
    return True


def run_simulated_fallback(x, y):
    """Thread-accurate NumPy simulation of the Numba kernel.

    For every block: (1) each of the 256 lanes loads x[g_id] into its shared
    tile lane when g_id < n, (2) a simulated syncthreads barrier, (3) each lane
    with 0 < t_id < 255 and g_id < n-1 averages its three shared neighbours.
    """
    print("[SIM] No CUDA -> simulating @cuda.jit kernel: shared tile load, "
          "syncthreads barrier, neighbour reads")
    out = np.zeros(N, dtype=np.float32)
    for blockIdx in range(BLOCKS_PER_GRID):
        base = THREADS_PER_BLOCK * blockIdx
        t_ids = np.arange(THREADS_PER_BLOCK, dtype=np.int32)
        g_ids = base + t_ids
        shared = np.zeros(THREADS_PER_BLOCK, dtype=np.float32)
        loaded = g_ids < np.int32(N)
        shared[loaded] = x[g_ids[loaded]]        # global -> shared load
        # ---- cuda.syncthreads(): all lanes wait here ----
        interior = (t_ids > 0) & (t_ids < 255) & (g_ids < np.int32(N - 1))
        t_calc = t_ids[interior]
        shared_reads = (shared[t_calc - 1] + shared[t_calc] +
                        shared[t_calc + 1]) / np.float32(3.0)
        out[g_ids[interior]] = shared_reads
    y[:] = out
    print("[SIM] {} blocks x {} threads executed with barrier semantics".format(
        BLOCKS_PER_GRID, THREADS_PER_BLOCK))


def reference_moving_average(x):
    """Independent CPU reference honouring the kernel's write conditions."""
    expected = np.zeros(N, dtype=np.float32)
    g = np.arange(N, dtype=np.int32)
    t_id = g % THREADS_PER_BLOCK
    valid = (t_id > 0) & (t_id < 255) & (g < N - 1)
    expected[valid] = ((x[g[valid] - 1] + x[g[valid]] + x[g[valid] + 1]) /
                       np.float32(3.0))
    return expected, valid


def main():
    """Launch (or simulate) the kernel and verify the filtered signal."""
    print("=" * 72)
    print("Exercise 4: Numba @cuda.jit Shared-Memory Moving Average")
    print("=" * 72)
    x, y = prepare_signal()
    print("signal: {} float32 samples, threads_per_block={}, blocks_per_grid={}".format(
        N, THREADS_PER_BLOCK, BLOCKS_PER_GRID))

    on_gpu = run_on_gpu(x, y)
    mode = "real NVIDIA GPU"
    if not on_gpu:
        run_simulated_fallback(x, y)
        mode = "CPU architectural simulation"
    print("[MODE] Execution path: {}".format(mode))

    expected, valid = reference_moving_average(x)
    max_err = float(np.max(np.abs(y - expected)))
    ok = bool(np.allclose(y, expected, rtol=1e-6, atol=1e-6))
    sample = int(np.argmax(valid))
    print("[CHECK] y[i] == (x[i-1] + x[i] + x[i+1]) / 3 on all lanes the kernel writes")
    print("        lanes written by kernel: {} of {} (t_id 0 and 255 of each block "
          "and last sample keep 0.0, per the spec's kernel conditions)".format(
              int(valid.sum()), N))
    print("        sample i={}: y={:.6f} expected={:.6f}, max abs err={:.3e}".format(
        sample, y[sample], expected[sample], max_err))
    print("[RESULT] " + ("PASS - filtered output matches the reference" if ok
                         else "FAIL - mismatch detected"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
