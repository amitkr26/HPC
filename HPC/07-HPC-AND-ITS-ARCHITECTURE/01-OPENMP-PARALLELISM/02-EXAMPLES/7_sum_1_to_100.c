/*
 * 7_sum_1_to_100.c
 * Calculates the sum of numbers 1 to 100 in parallel using
 * the reduction(+:sum) clause, which safely combines each
 * thread's partial sum into one final result.
 */
#include <stdio.h>
#include <omp.h>

int main() {
    int sum = 0;

    #pragma omp parallel for reduction(+:sum)
    for (int i = 1; i <= 100; i++) {
        sum += i;
    }

    printf("Sum of 1 to 100 = %d\n", sum);
    return 0;
}
