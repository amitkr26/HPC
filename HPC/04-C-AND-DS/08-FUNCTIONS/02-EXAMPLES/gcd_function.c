#include <stdio.h>

int gcd(int a, int b) {
    while(b != 0) {
        int temp = b;
        b = a % b;
        a = temp;
    }
    return a;
}

int main() {
    printf("GCD of 12 and 8 = %d\n", gcd(12, 8));
    printf("GCD of 15 and 25 = %d\n", gcd(15, 25));
    return 0;
}
