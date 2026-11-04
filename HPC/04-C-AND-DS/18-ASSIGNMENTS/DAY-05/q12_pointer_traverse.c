#include <stdio.h>

int main() {
    int arr[10] = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10};
    int *ptr;
    int i;

    ptr = arr;

    printf("Array elements using pointer arithmetic:\n");
    for (i = 0; i < 10; i++) {
        printf("%d ", *(ptr + i));
    }
    printf("\n");

    return 0;
}
