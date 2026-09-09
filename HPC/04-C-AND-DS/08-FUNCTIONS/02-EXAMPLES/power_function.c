#include <stdio.h>

int power(int base, int exp) {
    int result = 1, i;
    for(i = 0; i < exp; i++)
        result *= base;
    return result;
}

int main() {
    printf("2^10 = %d\n", power(2, 10));
    printf("3^5 = %d\n", power(3, 5));
    return 0;
}
