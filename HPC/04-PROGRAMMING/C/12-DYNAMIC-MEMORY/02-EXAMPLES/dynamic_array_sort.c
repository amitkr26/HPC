#include <stdio.h>
#include <stdlib.h>

void bubbleSort(int *arr, int n) {
    int i, j, temp;
    for(i = 0; i < n-1; i++) {
        for(j = 0; j < n-i-1; j++) {
            if(arr[j] > arr[j+1]) {
                temp = arr[j];
                arr[j] = arr[j+1];
                arr[j+1] = temp;
            }
        }
    }
}

int main() {
    int n, i;
    printf("Enter size: ");
    scanf("%d", &n);

    int *arr = (int*)malloc(n * sizeof(int));
    printf("Enter %d numbers: ", n);
    for(i = 0; i < n; i++) scanf("%d", &arr[i]);

    bubbleSort(arr, n);
    printf("Sorted: ");
    for(i = 0; i < n; i++) printf("%d ", arr[i]);
    printf("\n");

    free(arr);
    return 0;
}
