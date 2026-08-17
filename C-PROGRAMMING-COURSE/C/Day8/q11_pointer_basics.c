#include <stdio.h>

int main() {
    int num = 10;
    int *ptr;

    ptr = &num;

    printf("Value of num: %d\n", num);
    printf("Address of num (&num): %p\n", &num);
    printf("Value stored in ptr: %p\n", ptr);
    printf("Value via pointer (*ptr): %d\n", *ptr);

    return 0;
}
