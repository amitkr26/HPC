#include <stdio.h>

void swapByValue(int a, int b);
void swapByReference(int *a, int *b);

int main() {
    int x, y;

    printf("Enter two numbers: ");
    scanf("%d %d", &x, &y);

    printf("\nOriginal: x = %d, y = %d\n", x, y);

    swapByValue(x, y);
    printf("After swapByValue: x = %d, y = %d (no change)\n", x, y);

    swapByReference(&x, &y);
    printf("After swapByReference: x = %d, y = %d (swapped!)\n", x, y);

    return 0;
}

void swapByValue(int a, int b) {
    int temp = a;
    a = b;
    b = temp;
}

void swapByReference(int *a, int *b) {
    int temp = *a;
    *a = *b;
    *b = temp;
}
