#include <stdio.h>

int main() {
    int c=5;
    printf("c = %d\n", c); //5
    printf("++c = %d\n", ++c); // 6
    printf("--c = %d\n", --c); //5
    printf("c-- = %d\n", c--); //5
    printf("c++ = %d\n", c++); //4
    printf("c = %d", c); //5
    return 0;
}