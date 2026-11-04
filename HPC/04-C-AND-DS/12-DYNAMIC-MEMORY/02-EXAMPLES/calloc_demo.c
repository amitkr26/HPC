#include <stdio.h>
#include <stdlib.h>

int main() {
    int n = 5, i;
    int *arr = (int*)calloc(n, sizeof(int));

    printf("Calloc array (all zeros): ");
    for(i = 0; i < n; i++)
        printf("%d ", arr[i]);
    printf("\n");

    free(arr);
    return 0;
}
