#include <stdio.h>
#include <stdlib.h>

int main() {
    int n, i;
    printf("Enter size: ");
    scanf("%d", &n);

    int *arr = (int*)malloc(n * sizeof(int));
    if(arr == NULL) {
        printf("Memory allocation failed\n");
        return 1;
    }

    for(i = 0; i < n; i++)
        arr[i] = (i+1) * 10;

    printf("Array: ");
    for(i = 0; i < n; i++)
        printf("%d ", arr[i]);
    printf("\n");

    free(arr);
    return 0;
}
