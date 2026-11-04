#include <stdio.h>

int arrSum(int arr[], int n) {
    if(n == 0) return 0;
    return arr[n-1] + arrSum(arr, n-1);
}

int main() {
    int arr[] = {1, 2, 3, 4, 5};
    int n = 5;
    printf("Sum = %d\n", arrSum(arr, n));
    return 0;
}
