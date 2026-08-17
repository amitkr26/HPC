#include <stdio.h>

int reverseNum(int n);

int main() {
    int num;

    printf("Enter a number: ");
    scanf("%d", &num);

    printf("Reversed = %d\n", reverseNum(num));

    return 0;
}

int reverseNum(int n) {
    int rev = 0;

    while (n != 0) {
        rev = rev * 10 + n % 10;
        n = n / 10;
    }

    return rev;
}
