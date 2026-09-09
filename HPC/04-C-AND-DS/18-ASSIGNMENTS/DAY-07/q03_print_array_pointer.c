#include <stdio.h>

int main() {
    int arr[10] = {10, 20, 30, 40, 50, 60, 70, 80, 90, 100};
    int *ptr;
    int i;

    ptr = arr;

    printf("Array elements using pointer:\n");
    for (i = 0; i < 10; i++) {
        printf("%d ", *ptr);
        ptr++;
    }
    printf("\n");

    return 0;
}