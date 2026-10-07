"""Exercise 1: PyCUDA Vector Scaling & Memory Management.

Scales a 1D vector x of 65,536 float32 elements by alpha = 3.5 on the GPU
using a hand-written CUDA C kernel compiled through pycuda.compiler.SourceModule.

Kernel (as given in the problem statement):

    idx = blockDim.x * blockIdx.x + threadIdx.x
    if (idx < n): y[idx] = alpha * x[idx]

Block size is 256 threads, so the grid is sized (65536 // 256) = 256 blocks.

Data flow (the 5-step flow demonstrated in Day 5 Demo 01):
    1. Host allocation       2. Device allocation
    3. Host -> Device copy   4. Kernel execution
    5. Device -> Host copy

If neither the pycuda library nor an NVIDIA CUDA device is available, the script
runs the *identical* 5-step data flow as an architectural-simulation fallback
(device buffers and memcpy are emulated in NumPy, the kernel is evaluated with
its exact block/thread index arithmetic), then verifies the result against the
NumPy reference. All scalar kernel arguments are wrapped in NumPy fixed types
(np.float32(3.5), np.int32(65536)) as required by the spec.
"""

import numpy as np

N = 65536
ALPHA = 3.5
BLOCK_SIZE = 256
GRID_SIZE = N // BLOCK_SIZE

KERNEL_SRC = r"""
__global__ void scale_vector(float *y, const float *x, float alpha, int n) {
    int idx = blockDim.x * blockIdx.x + threadIdx.x;
    if (idx < n) {
        y[idx] = alpha * x[idx];
    }
}
"""


def prepare_host_vectors():
    """Step 1 material: allocate input x (65536 float32) and empty output y."""
    rng = np.random.default_rng(42)
    x = rng.standard_normal(N).astype(np.float32)
    y = np.empty_like(x)
    return x, y


def run_on_gpu(x, y):
    """Run the real CUDA path (steps 2-5) with PyCUDA.

    Returns True on success, False if pycuda or a CUDA device is unavailable
    (the caller then uses the simulation fallback).
    """
    try:
        import pycuda.driver as cuda
        import pycuda.autoinit  # noqa: F401  (creates the CUDA context)
        from pycuda.compiler import SourceModule
    except Exception as exc:
        print(f"[GPU] PyCUDA unavailable -> {type(exc).__name__}: {exc}")
        return False

    print("[1] Host allocation     : x, y = {} float32 ({} bytes each)".format(N, x.nbytes))
    print("[2] Device allocation   : cuda.mem_alloc(x.nbytes / y.nbytes)")
    dev_x = cuda.mem_alloc(x.nbytes)
    dev_y = cuda.mem_alloc(y.nbytes)
    print("[3] H2D copy            : cuda.memcpy_htod ({} bytes)".format(x.nbytes))
    cuda.memcpy_htod(dev_x, x)
    mod = SourceModule(KERNEL_SRC)
    func = mod.get_function("scale_vector")
    print("[4] Kernel launch       : scale_vector block=(256,1,1) grid=({},1)".format(GRID_SIZE))
    func(dev_y, dev_x, np.float32(ALPHA), np.int32(N),
         block=(BLOCK_SIZE, 1, 1), grid=(GRID_SIZE, 1))
    print("[5] D2H copy            : cuda.memcpy_dtoh ({} bytes)".format(y.nbytes))
    cuda.memcpy_dtoh(y, dev_y)
    return True


def run_simulated_fallback(x, y):
    """Architectural-simulation fallback: the exact same 5-step data flow.

    Device memory is emulated with NumPy arrays, memcpy_htod/memcpy_dtoh become
    array copies, and the CUDA kernel is evaluated with its literal index
    arithmetic (idx = blockDim.x * blockIdx.x + threadIdx.x, guarded by idx < n).
    """
    print("[SIM] No CUDA library/device available -> running the architectural-simulation fallback.")
    print("[SIM] Reproducing the identical 5-step data flow of Day 5 Demo 01:")
    print("  [1] Host allocation    : x, y = {} float32 ({} bytes each)".format(N, x.nbytes))
    dev_x = np.empty_like(x)
    dev_y = np.empty_like(y)
    print("  [2] Device allocation  : dev_x, dev_y = {} bytes of (simulated) device VRAM".format(x.nbytes))
    dev_x[:] = x
    print("  [3] H2D copy           : memcpy_htod {} bytes".format(x.nbytes))
    n_blocks = (N + BLOCK_SIZE - 1) // BLOCK_SIZE
    for blockIdx in range(n_blocks):
        base = BLOCK_SIZE * blockIdx
        idx = base + np.arange(BLOCK_SIZE, dtype=np.int32)
        mask = idx < np.int32(N)
        dev_y[idx[mask]] = np.float32(ALPHA) * dev_x[idx[mask]]
    print("  [4] Kernel execution   : scale_vector, {} blocks x {} threads".format(n_blocks, BLOCK_SIZE))
    y[:] = dev_y
    print("  [5] D2H copy           : memcpy_dtoh {} bytes".format(y.nbytes))


def main():
    """Prepare host data, run (or simulate) the GPU pipeline, verify results."""
    print("=" * 72)
    print("Exercise 1: PyCUDA Vector Scaling & Memory Management")
    print("=" * 72)
    x, y = prepare_host_vectors()
    print("alpha = {}, n = {}, dtype = {}, bytes = {} (matches array.nbytes)".format(
        ALPHA, N, x.dtype, x.nbytes))

    on_gpu = run_on_gpu(x, y)
    if not on_gpu:
        run_simulated_fallback(x, y)
    mode = "real NVIDIA GPU" if on_gpu else "CPU architectural simulation"
    print(f"[MODE] Execution path: {mode}")

    expected = np.float32(ALPHA) * x
    max_err = float(np.max(np.abs(y.astype(np.float64) - expected.astype(np.float64))))
    ok = bool(np.allclose(y, expected, rtol=1e-6, atol=1e-6))
    print("[CHECK] expected relation y[i] == 3.5 * x[i]")
    print("        max abs error = {:.3e}".format(max_err))
    print("        sample: x[0]={:.6f} y[0]={:.6f} (3.5*x[0]={:.6f})".format(x[0], y[0], expected[0]))
    print("[RESULT] " + ("PASS - all elements satisfy y[i] = 3.5 * x[i]" if ok
                        else "FAIL - mismatch detected"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
