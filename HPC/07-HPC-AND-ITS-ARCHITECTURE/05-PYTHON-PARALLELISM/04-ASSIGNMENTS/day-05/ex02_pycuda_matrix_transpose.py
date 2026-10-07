"""Exercise 2: 2D Matrix Transposition Kernel (PyCUDA).

Transposes a 512x512 matrix of sequential float32 values in parallel on the GPU
using a 2D CUDA kernel with 16x16 thread blocks.

Kernel (as given in the problem statement):

    col = blockIdx.x * blockDim.x + threadIdx.x     (X dimension = column)
    row = blockIdx.y * blockDim.y + threadIdx.y     (Y dimension = row)
    if (col < width && row < height):
        out[col * height + row] = in[row * width + col]

Flattened row-major index: index = row * width + col. The output uses the
transposed coordinates, so out holds in.T. Boundary checks prevent
out-of-bounds VRAM access when a dimension is not a multiple of 16.

Without pycuda or an NVIDIA GPU the script falls back to an architectural
simulation: the 2D grid/block launch is walked block by block in NumPy with the
exact threadIdx/blockIdx arithmetic and the same boundary condition, followed by
verification against the CPU-computed transpose.
"""

import numpy as np

WIDTH = 512
HEIGHT = 512
BLOCK = (16, 16)
GRID = (WIDTH // BLOCK[0], HEIGHT // BLOCK[1])

KERNEL_SRC = r"""
__global__ void transpose_matrix(float *out, const float *in, int width, int height) {
    int col = blockIdx.x * blockDim.x + threadIdx.x;
    int row = blockIdx.y * blockDim.y + threadIdx.y;
    if (col < width && row < height) {
        int in_idx  = row * width + col;
        int out_idx = col * height + row;
        out[out_idx] = in[in_idx];
    }
}
"""


def prepare_host_matrix():
    """Host setup: sequential matrix plus the CPU reference transpose."""
    n = np.arange(WIDTH * HEIGHT, dtype=np.float32)
    mat = n.reshape(HEIGHT, WIDTH)
    expected_T = np.ascontiguousarray(mat.T)
    return mat, expected_T


def run_on_gpu(mat, out):
    """Real CUDA path (steps 2-5). Returns False if PyCUDA/CUDA is unavailable."""
    try:
        import pycuda.driver as cuda
        import pycuda.autoinit  # noqa: F401
        from pycuda.compiler import SourceModule
    except Exception as exc:
        print(f"[GPU] PyCUDA unavailable -> {type(exc).__name__}: {exc}")
        return False

    print("[2] Device allocation   : cuda.mem_alloc({} bytes) x2".format(mat.nbytes))
    dev_in = cuda.mem_alloc(mat.nbytes)
    dev_out = cuda.mem_alloc(out.nbytes)
    print("[3] H2D copy            : {} bytes".format(mat.nbytes))
    cuda.memcpy_htod(dev_in, mat)
    mod = SourceModule(KERNEL_SRC)
    func = mod.get_function("transpose_matrix")
    print("[4] Kernel launch       : block=(16,16,1) grid=({},1)".format(GRID))
    func(dev_out, dev_in, np.int32(WIDTH), np.int32(HEIGHT),
         block=(BLOCK[0], BLOCK[1], 1), grid=GRID)
    print("[5] D2H copy            : {} bytes".format(out.nbytes))
    cuda.memcpy_dtoh(out, dev_out)
    return True


def run_simulated_fallback(mat, out):
    """Architectural-simulation fallback: emulate the 2D grid launch in NumPy.

    Every (blockIdx.x, blockIdx.y) block is visited; inside a block the
    threadIdx.x/y coordinates are built as 16x16 tiles, the boundary condition
    (col < width && row < height) is applied, and the flat indices
    in_idx = row*width + col / out_idx = col*height + row are used - i.e. the
    literal kernel body, evaluated per simulated block.
    """
    print("[SIM] No CUDA library/device -> architectural-simulation fallback (2D grid walk).")
    dev_in = mat.ravel().copy()          # linear device buffer, as CUDA sees it
    dev_out = np.empty(HEIGHT * WIDTH, dtype=np.float32)
    threads_x, threads_y = BLOCK
    for by in range(GRID[1]):
        for bx in range(GRID[0]):
            row = by * threads_y + np.arange(threads_y, dtype=np.int32)
            col = bx * threads_x + np.arange(threads_x, dtype=np.int32)
            rr, cc = np.meshgrid(row, col, indexing="ij")
            mask = (cc < WIDTH) & (rr < HEIGHT)
            in_idx = rr * WIDTH + cc
            out_idx = cc * HEIGHT + rr
            dev_out[out_idx[mask]] = dev_in[in_idx[mask]]
    out[:] = dev_out.reshape(HEIGHT, WIDTH)
    print("[SIM] Walked {} 2D blocks of 16x16 threads ({} threads total).".format(
        GRID[0] * GRID[1], GRID[0] * GRID[1] * threads_x * threads_y))


def main():
    """Run the transpose on GPU (or simulated), assert against CPU transpose."""
    print("=" * 72)
    print("Exercise 2: 2D Matrix Transposition Kernel")
    print("=" * 72)
    mat, expected_T = prepare_host_matrix()
    out = np.empty_like(mat)
    print("matrix {}x{} float32 ({} bytes), block={}, grid={}".format(
        HEIGHT, WIDTH, mat.nbytes, BLOCK, GRID))

    on_gpu = run_on_gpu(mat, out)
    if not on_gpu:
        run_simulated_fallback(mat, out)
    print(f"[MODE] Execution path: {'real NVIDIA GPU' if on_gpu else 'CPU architectural simulation'}")

    print("[CHECK] comparing GPU output against CPU transpose (mat.T)")
    assert np.array_equal(out, expected_T), "GPU transpose does not match CPU transpose!"
    print("[RESULT] PASS - output matches the CPU transpose exactly "
          "(sample out[0,0]={}, out[0,1]={} vs expected {}, {})".format(
              out[0, 0], out[0, 1], expected_T[0, 0], expected_T[0, 1]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
