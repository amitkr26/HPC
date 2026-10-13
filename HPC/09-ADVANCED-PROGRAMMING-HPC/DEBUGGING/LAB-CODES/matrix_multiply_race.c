// Lab 4b: OpenMP data race. 'sum' is declared outside the parallel loop,
// so it is shared by all threads. Compare with a serial reference. N is large so the race shows up reliably.
#include <stdio.h>
#include <omp.h>
#define N 256

int A[N][N], B[N][N], C[N][N], R[N][N];

int main() {
    for (int i = 0; i < N; i++)
        for (int j = 0; j < N; j++) { A[i][j] = i + j; B[i][j] = i - j; }

    for (int i = 0; i < N; i++)                // serial reference
        for (int j = 0; j < N; j++) {
            int s = 0;
            for (int k = 0; k < N; k++) s += A[i][k] * B[k][j];
            R[i][j] = s;
        }

    int sum = 0;                               // BUG: shared between threads
    #pragma omp parallel for collapse(2)
    for (int i = 0; i < N; i++) {
        for (int j = 0; j < N; j++) {
            sum = 0;
            for (int k = 0; k < N; k++) {
                sum += A[i][k] * B[k][j];
            }
            C[i][j] = sum;
        }
    }

    int bad = 0;
    for (int i = 0; i < N; i++)
        for (int j = 0; j < N; j++)
            if (C[i][j] != R[i][j]) bad++;
    printf("Mismatches vs serial: %d (threads: %d)\n", bad, omp_get_max_threads());
    return 0;
}
