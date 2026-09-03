#include <stdio.h>

int main() {
    int arr[5] = {10, 20, 30, 40, 50};
    int *ptr;
    int i;
    int sum = 0;
    float average;

    ptr = arr;

    for (i = 0; i < 5; i++) {
        sum = sum + *ptr;
        ptr++;
    }

    average = (float)sum / 5;

    printf("Array: ");
    ptr = arr;
    for (i = 0; i < 5; i++) {
        printf("%d ", *ptr);
        ptr++;
    }

    printf("\nSum = %d\n", sum);
    printf("Average = %.2f\n", average);

    return 0;
}
