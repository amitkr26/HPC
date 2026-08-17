#include <stdio.h>

void countEvenOdd(int *arr, int n, int *even, int *odd) {
    *even = *odd = 0;
    int i;
    for(i = 0; i < n; i++) {
        if(*(arr + i) % 2 == 0)
            (*even)++;
        else
            (*odd)++;
    }
}

int main() {
    int arr[] = {1, 2, 3, 4, 5, 6, 7, 8};
    int n = 8, even, odd;
    countEvenOdd(arr, n, &even, &odd);
    printf("Even: %d, Odd: %d\n", even, odd);
    return 0;
}
