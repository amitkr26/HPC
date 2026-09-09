#include <stdio.h>

int *findLargest(int *arr, int n) {
    int *largest = arr;
    int i;
    for(i = 1; i < n; i++) {
        if(*(arr+i) > *largest)
            largest = arr + i;
    }
    return largest;
}

int main() {
    int arr[] = {23, 56, 11, 89, 45};
    int n = 5;
    int *result = findLargest(arr, n);
    printf("Array: ");
    int i;
    for(i = 0; i < n; i++) printf("%d ", arr[i]);
    printf("\nLargest: %d\n", *result);
    return 0;
}
