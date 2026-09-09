#include <stdio.h>

int main() {
    int x = 100;
    int *ptr = &x;
    int **pptr = &ptr;

    printf("x = %d\n", x);
    printf("*ptr = %d\n", *ptr);
    printf("**pptr = %d\n", **pptr);
    printf("\nAddress of x: %p\n", (void*)&x);
    printf("ptr stores: %p\n", (void*)ptr);
    printf("pptr stores: %p\n", (void*)pptr);

    return 0;
}
