#include <stdio.h>

int main() {
    int num = 42;
    int *ptr = &num;
    int **pptr = &ptr;

    printf("Value of the variable: %d\n", num);
    printf("Address of the variable (&num): %p\n", &num);
    printf("Value stored in the pointer (ptr): %p\n", ptr);
    printf("Address of the pointer (&ptr): %p\n", &ptr);
    printf("Value stored in the double pointer (*pptr): %p\n", *pptr);
    printf("Address of the double pointer (&pptr): %p\n", &pptr);

    return 0;
}
