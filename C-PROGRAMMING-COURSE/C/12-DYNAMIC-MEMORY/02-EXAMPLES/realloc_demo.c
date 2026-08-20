#include <stdio.h>
#include <stdlib.h>

int main() {
    int n = 3, i;
    int *arr = (int*)malloc(n * sizeof(int));

    for(i = 0; i < n; i++) arr[i] = i + 1;
    printf("Before realloc: ");
    for(i = 0; i < n; i++) printf("%d ", arr[i]);
    printf("\n");

    n = 5;
    arr = (int*)realloc(arr, n * sizeof(int));
    for(i = 3; i < n; i++) arr[i] = i + 1;

    printf("After realloc: ");
    for(i = 0; i < n; i++) printf("%d ", arr[i]);
    printf("\n");

    free(arr);
    return 0;
}
