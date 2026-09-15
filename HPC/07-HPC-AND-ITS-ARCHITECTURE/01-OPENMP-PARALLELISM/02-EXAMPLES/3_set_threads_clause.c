/*
 * 3_set_threads_clause.c
 * Sets the number of threads to 8 using the num_threads() CLAUSE
 * directly on the #pragma omp parallel directive.
 */
#include <stdio.h>
#include <omp.h>

int main() {
    #pragma omp parallel num_threads(8)   // clause -> requests 8 threads
    {
        printf("Thread %d of %d (set via num_threads clause)\n",
               omp_get_thread_num(), omp_get_num_threads());
    }
    return 0;
}
