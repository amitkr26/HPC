#include <stdio.h>

int arraySum(int *arr, int n) {
    int sum = 0, i;
    for(i = 0; i < n; i++)
        sum += *(arr + i);
    return sum;
}

int main() {
    int arr[] = {1, 2, 3, 4, 5};
    int n = 5;
    printf("Sum = %d\n", arraySum(arr, n));
    return 0;
}
