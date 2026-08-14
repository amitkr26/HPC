#include <stdio.h>

int main() {
    int arr[10] = {5, 12, 15, 20, 23, 25, 30, 35, 42, 50};
    int *ptr;
    int count = 0;
    int i;

    ptr = arr;

    for (i = 0; i < 10; i++) {
        if (*ptr % 5 == 0) {
            count++;
        }
        ptr++;
    }

    printf("Array elements: ");
    ptr = arr;
    for (i = 0; i < 10; i++) {
        printf("%d ", *ptr);
        ptr++;
    }

    printf("\nElements divisible by 5: %d\n", count);

    return 0;
}
