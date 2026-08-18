#include <stdio.h>

int main() {
    int arr[10] = {12, 5, 8, 7, 10, 3, 6, 9, 14, 1};
    int *ptr;
    int even = 0, odd = 0;
    int i;

    ptr = arr;

    for (i = 0; i < 10; i++) {
        if (*ptr % 2 == 0)
            even++;
        else
            odd++;
        ptr++;
    }

    printf("Array elements: ");
    ptr = arr;
    for (i = 0; i < 10; i++) {
        printf("%d ", *ptr);
        ptr++;
    }

    printf("\nEven numbers: %d\n", even);
    printf("Odd numbers: %d\n", odd);

    return 0;
}
