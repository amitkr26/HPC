// Lab 5 (optional): CUDA-GDB demo. Not compiled here (needs nvcc + GPU).
// Bug: no bounds check, and the grid is rounded up, so threads with
// idx >= n write out of bounds. Try:  compute-sanitizer ./vector_add
#include <cstdio>

__global__ void vector_add(const float *a, const float *b, float *c, int n) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    // BUG: missing  if (idx < n)
    c[idx] = a[idx] + b[idx];
}

int main() {
    const int n = 1000, bytes = n * sizeof(float);
    float *a, *b, *c;
    cudaMallocManaged(&a, bytes);
    cudaMallocManaged(&b, bytes);
    cudaMallocManaged(&c, bytes);
    for (int i = 0; i < n; i++) { a[i] = i; b[i] = 2 * i; }

    int threads = 256, blocks = (n + threads - 1) / threads;   // 4 blocks = 1024 threads
    vector_add<<<blocks, threads>>>(a, b, c, n);
    cudaDeviceSynchronize();

    printf("c[10]=%.1f c[999]=%.1f\n", c[10], c[999]);
    cudaFree(a); cudaFree(b); cudaFree(c);
    return 0;
}
