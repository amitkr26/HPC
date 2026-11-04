// Lab 4a: correct OpenMP matrix multiplication (sum is private).
#include <stdio.h>
#include <omp.h>
#define N 8

int A[N][N], B[N][N], C[N][N];

int main() {
    for (int i = 0; i < N; i++)
        for (int j = 0; j < N; j++) { A[i][j] = i + j; B[i][j] = i - j; }

    #pragma omp parallel for collapse(2)
    for (int i = 0; i < N; i++) {
        for (int j = 0; j < N; j++) {
            int sum = 0;                       // private: declared inside
            for (int k = 0; k < N; k++) {
                sum += A[i][k] * B[k][j];
            }
            C[i][j] = sum;
        }
    }

    printf("C[0][0]=%d C[%d][%d]=%d\n", C[0][0], N-1, N-1, C[N-1][N-1]);
    return 0;
}
