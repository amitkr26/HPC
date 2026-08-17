#include <stdio.h>

int main() {
    int arr[6] = {45, 12, 78, 34, 99, 8};
    int *ptr;
    int i;
    int max, min;

    ptr = arr;

    max = *ptr;
    min = *ptr;

    for (i = 0; i < 6; i++) {
        if (*ptr > max) {
            max = *ptr;
        }
        if (*ptr < min) {
            min = *ptr;
        }
        ptr++;
    }

    printf("Array elements: ");
    ptr = arr;
    for (i = 0; i < 6; i++) {
        printf("%d ", *ptr);
        ptr++;
    }

    printf("\nMaximum value = %d\n", max);
    printf("Minimum value = %d\n", min);

    return 0;
}
