/*
 * 1_show_thread_info.c
 * Shows the current thread's ID and the total number of threads
 * running in the parallel region.
 */
#include <stdio.h>
#include <omp.h>

int main() {
    #pragma omp parallel
    {
        int tid = omp_get_thread_num();      // ID of the calling thread
        int nthreads = omp_get_num_threads(); // total threads in this region

        printf("Hello from thread %d of %d\n", tid, nthreads);
    }
    return 0;
}
