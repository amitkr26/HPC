#include <stdio.h>

int main() {
    int num = 42;
    int *ptr;

    ptr = &num;

    printf("Value directly: %d\n", num);
    printf("Value via pointer dereferencing: %d\n", *ptr);
    printf("Address of num (&variable): %p\n", &num);

    return 0;
}