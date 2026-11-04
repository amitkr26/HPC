#include <stdio.h>

int main() {
    int arr[5] = {23, 45, 67, 12, 89};
    int *ptr;
    int i, max;

    ptr = arr;
    max = *ptr;

    for (i = 1; i < 5; i++) {
        ptr++;
        if (*ptr > max)
            max = *ptr;
    }

    printf("Array: ");
    for (i = 0; i < 5; i++)
        printf("%d ", arr[i]);

    printf("\nLargest element = %d\n", max);

    return 0;
}
