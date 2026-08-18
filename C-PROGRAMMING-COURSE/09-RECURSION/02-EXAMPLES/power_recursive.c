#include <stdio.h>

int power(int base, int exp) {
    if(exp == 0) return 1;
    return base * power(base, exp - 1);
}

int main() {
    printf("2^10 = %d\n", power(2, 10));
    printf("3^5 = %d\n", power(3, 5));
    return 0;
}
