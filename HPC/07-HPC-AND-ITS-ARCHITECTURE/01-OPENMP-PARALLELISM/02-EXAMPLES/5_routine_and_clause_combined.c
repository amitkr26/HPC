/*
 * 5_routine_and_clause_combined.c
 * Sets threads to 10 via omp_set_num_threads() (routine call),
 * AND sets threads to 8 via the num_threads() clause on the
 * SAME parallel region.
 *
 * When run WITHOUT the OMP_NUM_THREADS environment variable, this
 * lets us see which one wins: the clause or the routine call.
 *
 * Run it as:  ./5_routine_and_clause_combined
 * (no env var set)
 */
#include <stdio.h>
#include <omp.h>

int main() {
    omp_set_num_threads(10);              // routine call requests 10

    #pragma omp parallel num_threads(8)   // clause requests 8
    {
        printf("Thread %d of %d (routine=10, clause=8)\n",
               omp_get_thread_num(), omp_get_num_threads());
    }
    return 0;
}
