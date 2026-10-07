"""Exercise 3: High-Level GPU Arrays & Custom Elementwise Expressions.

Demonstrates PyCUDA's high-level abstractions instead of raw SourceModule code:

1. pycuda.gpuarray - two 500,000-element float32 vectors u and v are pushed to
   GPU memory with gpuarray.to_gpu(), the linear combination
   w = 2.0*u + 5.0*v - 1.0 is evaluated directly in VRAM with ordinary Python
   operators (GPUArray overloads them into kernel launches), and the result is
   fetched back with .get() and checked against CPU NumPy. GPUArray also offers
   parallel reductions such as .sum(), .max(), .min().
2. pycuda.ElementwiseKernel - a custom element-wise kernel applies the ReLU
   activation f(x) = max(0, x):

       relu_kernel = ElementwiseKernel(
           "float *out, const float *in",
           "out[i] = (in[i] > 0.0f) ? in[i] : 0.0f",
           "relu_activation")

   ElementwiseKernel derives block/grid dimensions and indexing automatically.

Without pycuda (or a CUDA device) the script falls back to a NumPy simulation
of the same transfer-and-compute pipeline, then verifies results against the
NumPy reference.
"""

import numpy as np

N = 500_000

RELU_KERNEL_SRC = """
out[i] = (in[i] > 0.0f) ? in[i] : 0.0f
"""


def prepare_host_data():
    """Host vectors: u, v random float32 (seeded) and a mixed-sign ReLU input."""
    rng = np.random.default_rng(7)
    u = rng.standard_normal(N).astype(np.float32)
    v = rng.standard_normal(N).astype(np.float32)
    relu_in = rng.standard_normal(1024).astype(np.float32)
    relu_in[::2] = -np.abs(relu_in[::2])  # guarantee negatives
    relu_in[1::2] = np.abs(relu_in[1::2])  # and positives
    return u, v, relu_in


def run_linear_combination_gpu(u, v):
    """GPUArray path: to_gpu -> operator math in VRAM -> .get(). Returns w or None."""
    try:
        import pycuda.autoinit  # noqa: F401
        from pycuda import gpuarray
    except Exception as exc:
        print(f"[GPU] PyCUDA unavailable -> {type(exc).__name__}: {exc}")
        return None

    print("[GPU] gpuarray.to_gpu(): u, v -> device ({} float32 each)".format(u.size))
    d_u = gpuarray.to_gpu(u)
    d_v = gpuarray.to_gpu(v)
    print("[GPU] evaluating w = 2.0*u + 5.0*v - 1.0 directly in device memory")
    d_w = np.float32(2.0) * d_u + np.float32(5.0) * d_v - np.float32(1.0)
    print("[GPU] parallel reductions on device: w.sum() = {:.4f}".format(d_w.sum()))
    return d_w.get()


def run_linear_combination_simulated(u, v):
    """Simulation of steps 2-5 for the linear combination (H2D -> compute -> D2H)."""
    print("[SIM] No CUDA -> simulation: host -> 'device' copy -> operator compute -> copy back")
    dev_u = u.copy()
    dev_v = v.copy()
    dev_w = np.float32(2.0) * dev_u + np.float32(5.0) * dev_v - np.float32(1.0)
    print("[SIM] simulated device reduction: w.sum() = {:.4f}".format(dev_w.sum()))
    return dev_w.copy()


def relu_reference(x):
    """CPU reference for f(x) = max(0, x) in float32."""
    return np.maximum(x, np.float32(0.0))


def run_relu_gpu(x):
    """ElementwiseKernel path. Returns result array or None if unavailable."""
    try:
        import pycuda.autoinit  # noqa: F401
        from pycuda import gpuarray
        from pycuda.elementwise import ElementwiseKernel
    except Exception as exc:
        print(f"[GPU] PyCUDA unavailable -> {type(exc).__name__}: {exc}")
        return None

    relu_kernel = ElementwiseKernel(
        "float *out, const float *in",
        "out[i] = (in[i] > 0.0f) ? in[i] : 0.0f",
        "relu_activation")
    d_in = gpuarray.to_gpu(x)
    d_out = gpuarray.empty_like(d_in)
    print("[GPU] launching ElementwiseKernel 'relu_activation' over {} elements".format(x.size))
    relu_kernel(d_out, d_in)
    return d_out.get()


def run_relu_simulated(x):
    """Simulation of the ReLU element-wise kernel on the 'device'."""
    print("[SIM] Simulating ElementwiseKernel 'relu_activation' (out[i] = in[i] > 0 ? in[i] : 0)")
    return relu_reference(x)


def main():
    """Execute both parts, verify against CPU NumPy."""
    print("=" * 72)
    print("Exercise 3: High-Level GPU Arrays & Custom Elementwise Expressions")
    print("=" * 72)
    u, v, relu_in = prepare_host_data()
    print("u, v: {} random float32 values each".format(N))

    print("\n--- Part 1: GPUArray arithmetic  w = 2.0*u + 5.0*v - 1.0 ---")
    w = run_linear_combination_gpu(u, v)
    mode = "real NVIDIA GPU"
    if w is None:
        w = run_linear_combination_simulated(u, v)
        mode = "CPU architectural simulation"
    expected_w = np.float32(2.0) * u + np.float32(5.0) * v - np.float32(1.0)
    ok1 = bool(np.allclose(w, expected_w, rtol=1e-5, atol=1e-5))
    print("[CHECK] allclose(w, numpy 2.0*u + 5.0*v - 1.0) -> {} (max abs err {:.3e})".format(
        ok1, float(np.max(np.abs(w - expected_w)))))

    print("\n--- Part 2: ElementwiseKernel ReLU  f(x) = max(0, x) ---")
    relu_out = run_relu_gpu(relu_in)
    if relu_out is None:
        relu_out = run_relu_simulated(relu_in)
    expected_relu = relu_reference(relu_in)
    negatives = relu_in < 0
    positives = relu_in > 0
    ok2 = bool(np.all(relu_out[negatives] == 0.0) and
               np.allclose(relu_out[positives], relu_in[positives], rtol=0, atol=0) and
               np.array_equal(relu_out, expected_relu))
    print("[CHECK] {} negatives clamped to 0 -> {}".format(int(negatives.sum()),
                                                           bool(np.all(relu_out[negatives] == 0.0))))
    print("[CHECK] {} positives unchanged    -> {}".format(int(positives.sum()),
                                                           bool(np.all(relu_out[positives] == relu_in[positives]))))
    print("\n[MODE] Execution path: {}".format(mode))
    print("[RESULT] " + ("PASS - both parts verified against CPU NumPy" if ok1 and ok2
                         else "FAIL - mismatch detected"))
    return 0 if (ok1 and ok2) else 1


if __name__ == "__main__":
    raise SystemExit(main())
