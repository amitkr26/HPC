/*
 * 2_set_threads_routine_call.c
 * Sets the number of threads to 10 using the OpenMP RUNTIME LIBRARY
 * ROUTINE omp_set_num_threads(), which must be called before the
 * parallel region.
 */
#include <stdio.h>
#include <omp.h>

int main() {
    omp_set_num_threads(10);   // routine call -> requests 10 threads

    #pragma omp parallel
    {
        printf("Thread %d of %d (set via routine call)\n",
               omp_get_thread_num(), omp_get_num_threads());
    }
    return 0;
}
