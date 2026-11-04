#include <stdio.h>

int main() {
    int myage =23;
    int *ptr = &myage;
    printf("%d\n", myage);
    printf("%p\n", &myage);
    printf("%p\n", ptr);


    return 0;
}