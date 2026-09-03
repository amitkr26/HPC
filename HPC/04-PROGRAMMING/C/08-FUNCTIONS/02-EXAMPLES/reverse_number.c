#include <stdio.h>

int reverseNumber(int n) {
    int reversed = 0, remainder;
    while(n > 0) {
        remainder = n % 10;
        reversed = reversed * 10 + remainder;
        n /= 10;
    }
    return reversed;
}

int main() {
    printf("Reverse of 1234 = %d\n", reverseNumber(1234));
    printf("Reverse of 5678 = %d\n", reverseNumber(5678));
    return 0;
}
