#include <stdio.h>

void bubbleSort(int arr[], int n) {
    int i, temp;
    if(n <= 1) return;
    for(i = 0; i < n-1; i++) {
        if(arr[i] > arr[i+1]) {
            temp = arr[i];
            arr[i] = arr[i+1];
            arr[i+1] = temp;
        }
    }
    bubbleSort(arr, n-1);
}

int main() {
    int arr[] = {64, 34, 25, 12, 22};
    int n = 5, i;
    bubbleSort(arr, n);
    for(i = 0; i < n; i++) printf("%d ", arr[i]);
    printf("\n");
    return 0;
}
