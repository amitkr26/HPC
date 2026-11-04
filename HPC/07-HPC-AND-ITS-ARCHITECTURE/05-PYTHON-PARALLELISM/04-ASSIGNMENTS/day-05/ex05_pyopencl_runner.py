"""Exercise 5: Cross-Platform Accelerator Discovery & OpenCL Kernels.

Two phases:

1. Hardware discovery - pyopencl.cl.get_platforms() enumerates every OpenCL
   platform on the machine; each platform's devices are listed with name,
   vendor, device type (GPU/CPU/accelerator) and maximum compute units.
   device.max_work_group_size is reported so work-group sizes can be checked
   against hardware limits.

2. Kernel build & run - an OpenCL C kernel performs element-wise vector
   multiplication:

       __kernel void vector_mult(__global const float *a,
                                 __global const float *b,
                                 __global float *c) {
           int gid = get_global_id(0);
           c[gid] = a[gid] * b[gid];
       }

   The program is compiled with cl.Program(ctx, kernel_code).build(), read-only
   buffers are created for a and b (cl.mem_flags.READ_ONLY), a write-only
   buffer for c, the kernel is enqueued with global work size == vector length,
   and the result is read back and verified. A single OpenCL work-item
   corresponds to a CUDA thread (get_global_id(0) <-> cuda.grid(1)), and the
   kernel runs unchanged on NVIDIA, AMD, Intel or Apple Silicon devices.

If pyopencl is missing or no OpenCL platform/device is installed, the script
prints a clear notice and runs a NumPy architectural simulation of the same
host -> buffer -> enqueue -> read-back pipeline so it stays runnable on any
machine.
"""

import numpy as np

N = 1_000_000
LOCAL_SIZE = 64

KERNEL_SRC = """
__kernel void vector_mult(__global const float *a,
                          __global const float *b,
                          __global float *c) {
    int gid = get_global_id(0);
    c[gid] = a[gid] * b[gid];
}
"""

DEVICE_TYPE_NAMES = {
    "GPU": 1 << 2,  # cl.device_type.GPU
    "CPU": 1 << 1,  # cl.device_type.CPU
    "ACCELERATOR": 1 << 3,
    "DEFAULT": 1 << 0,
}


def prepare_host_data():
    """Host vectors a and b (1,000,000 random float32 each, seeded)."""
    rng = np.random.default_rng(2024)
    a = rng.standard_normal(N).astype(np.float32)
    b = rng.standard_normal(N).astype(np.float32)
    return a, b


def discover_platforms():
    """Phase 1: enumerate OpenCL platforms and device capabilities.

    Returns the imported pyopencl module on success, None if pyopencl is not
    installed or no platform could be found.
    """
    print("--- Phase 1: Hardware discovery (cl.get_platforms()) ---")
    try:
        import pyopencl as cl
    except Exception as exc:
        print("[DISCOVERY] pyopencl unavailable -> {} : {}".format(type(exc).__name__, exc))
        print("[DISCOVERY] Install with: pip install pyopencl (plus an OpenCL runtime/driver).")
        return None

    platforms = cl.get_platforms()
    if not platforms:
        print("[DISCOVERY] No OpenCL platforms found on this system.")
        return None

    found_device = False
    for p_idx, plat in enumerate(platforms):
        print("Platform {}: {} ({})".format(p_idx, plat.name, plat.vendor))
        for d_idx, dev in enumerate(plat.get_devices()):
            dtype = str(dev.type)
            dtype_name = ", ".join(name for name, bit in DEVICE_TYPE_NAMES.items()
                                   if dev.type & bit) or dtype
            print("  Device {}.{}: {}".format(p_idx, d_idx, dev.name))
            print("      vendor          : {}".format(dev.vendor))
            print("      device type     : {}".format(dtype_name))
            print("      compute units   : {}".format(dev.max_compute_units))
            print("      max work-group : {}".format(dev.max_work_group_size))
            found_device = True
    if not found_device:
        print("[DISCOVERY] Platforms found but no devices exposed.")
        return None
    return cl


def run_opencl_kernel(cl, a, b):
    """Phase 2: build the OpenCL program, transfer buffers, launch, read back.

    Returns (result, note) on success or (None, reason) if the context/kernel
    could not be created (e.g. driver build failure).
    """
    print("\n--- Phase 2: Build & run OpenCL kernel 'vector_mult' ---")
    try:
        ctx = cl.Context(devices=[d for p in cl.get_platforms()
                                  for d in p.get_devices()])
        queue = cl.CommandQueue(ctx)
        print("[CTX] context + command queue created")
        if not ctx.devices:
            return None, "context has no devices"
        max_wg = min(d.max_work_group_size for d in ctx.devices)
        if LOCAL_SIZE > max_wg:
            print("[WARN] local size {} exceeds max_work_group_size {}".format(LOCAL_SIZE, max_wg))
        mf = cl.mem_flags
        buf_a = cl.Buffer(ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=a)
        buf_b = cl.Buffer(ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=b)
        buf_c = cl.Buffer(ctx, mf.WRITE_ONLY, a.nbytes)
        print("[BUF] buffers created: a, b READ_ONLY; c WRITE_ONLY ({} bytes each)".format(a.nbytes))
        prg = cl.Program(ctx, KERNEL_SRC).build()
        print("[BUILD] cl.Program(...).build() succeeded")
        prg.vector_mult(queue, (N,), (LOCAL_SIZE,), buf_a, buf_b, buf_c)
        print("[ENQUEUE] kernel enqueued: global work size = {}, local size = {}".format(N, LOCAL_SIZE))
        c = np.empty(N, dtype=np.float32)
        cl.enqueue_copy(queue, c, buf_c).wait()
        print("[READ] result copied back to host memory")
        return c, "real OpenCL device"
    except Exception as exc:
        return None, "OpenCL execution failed -> {} : {}".format(type(exc).__name__, exc)


def run_simulated_fallback(a, b):
    """NumPy simulation of the OpenCL pipeline: buffer alloc -> enqueue -> read back."""
    print("[SIM] Running CPU architectural simulation of the OpenCL pipeline:")
    print("  [BUF] host arrays a, b treated as 'device buffers' ({} float32, {} bytes)".format(
        N, a.nbytes))
    dev_a = a.copy()
    dev_b = b.copy()
    dev_c = np.empty(N, dtype=np.float32)
    gid = np.arange(N, dtype=np.int32)
    dev_c[gid] = dev_a[gid] * dev_b[gid]   # c[gid] = a[gid] * b[gid], gid = get_global_id(0)
    print("  [ENQUEUE] vector_mult over {} work-items (get_global_id(0) = 0..{})".format(N, N - 1))
    c = dev_c.copy()
    print("  [READ] enqueue_copy back to host")
    return c, "CPU architectural simulation"


def main():
    """Discover accelerators, run the kernel (real or simulated), verify."""
    print("=" * 72)
    print("Exercise 5: Cross-Platform Accelerator Discovery & OpenCL Kernels")
    print("=" * 72)
    a, b = prepare_host_data()
    print("vectors: {} float32 elements each\n".format(N))

    cl = discover_platforms()
    c, mode = (None, "no OpenCL runtime")
    if cl is not None:
        c, mode = run_opencl_kernel(cl, a, b)
        if c is None:
            print("[NOTICE] " + mode)
    if c is None:
        c, mode = run_simulated_fallback(a, b)

    expected = a * b
    exact = bool(np.array_equal(c, expected))
    ok = bool(np.allclose(c, expected, rtol=1e-6, atol=1e-6))
    print("\n[MODE] Execution path: {}".format(mode))
    print("[CHECK] c[i] == a[i] * b[i] for all {} elements -> allclose={}".format(N, ok))
    print("        sample: a[0]={:.6f} b[0]={:.6f} c[0]={:.6f} (exact match={})".format(
        a[0], b[0], c[0], bool(np.isclose(c[0], expected[0]))))
    print("[RESULT] " + ("PASS - vector multiplication verified" if ok
                         else "FAIL - mismatch detected"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
