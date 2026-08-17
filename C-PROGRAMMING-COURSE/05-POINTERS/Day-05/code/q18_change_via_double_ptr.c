#include <stdio.h>

int main() {
    int num = 10;
    int *ptr = &num;
    int **pptr = &ptr;

    printf("Original value: %d\n", num);

    **pptr = 50;

    printf("Value changed using double pointer: %d\n", num);

    return 0;
}
