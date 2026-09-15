/*
 * 4_set_threads_env_var.c
 * This program itself sets NOTHING in code. The thread count is
 * controlled purely by the OMP_NUM_THREADS environment variable
 * set before running the executable, e.g.:
 *
 *     OMP_NUM_THREADS=4 ./4_set_threads_env_var
 */
#include <stdio.h>
#include <omp.h>

int main() {
    #pragma omp parallel
    {
        printf("Thread %d of %d (set via OMP_NUM_THREADS env var)\n",
               omp_get_thread_num(), omp_get_num_threads());
    }
    return 0;
}
