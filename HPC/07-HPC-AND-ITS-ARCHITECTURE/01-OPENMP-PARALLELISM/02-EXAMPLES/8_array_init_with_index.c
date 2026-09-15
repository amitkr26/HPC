/*
 * 8_array_init_with_index.c
 * Initializes an array of 10 integers so that each element equals
 * its own index, using a parallel for loop. Each thread writes to
 * a different element, so there is no race condition.
 */
#include <stdio.h>
#include <omp.h>

#define SIZE 10

int main() {
    int arr[SIZE];

    #pragma omp parallel for
    for (int i = 0; i < SIZE; i++) {
        arr[i] = i;
    }

    for (int i = 0; i < SIZE; i++) {
        printf("arr[%d] = %d\n", i, arr[i]);
    }
    return 0;
}
