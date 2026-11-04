#include <stdio.h>

int main() {
    int arr[7] = {1, 2, 3, 4, 5, 6, 7};
    int *left, *right;
    int temp;
    int i;

    printf("Original array: ");
    for (i = 0; i < 7; i++)
        printf("%d ", arr[i]);
    printf("\n");

    left = arr;
    right = arr + 6;

    while (left < right) {
        temp = *left;
        *left = *right;
        *right = temp;
        left++;
        right--;
    }

    printf("Reversed array: ");
    for (i = 0; i < 7; i++)
        printf("%d ", arr[i]);
    printf("\n");

    return 0;
}
