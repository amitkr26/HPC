// Lab 3: watchpoints and conditional breakpoints.
// Fixed: long long holds up to 20! (21! overflows even long long).
#include <stdio.h>

long long factorial(int n) {
    long long result = 1;
    for (int i = 1; i <= n; i++) {
        result *= i;
    }
    return result;
}

int main() {
    int number;

    printf("Enter a positive integer: ");
    if (scanf("%d", &number) != 1) return 1;

    if (number < 0) {
        printf("Error: Factorial of a negative number doesn't exist.\n");
        return 1;
    }

    long long fact = factorial(number);
    printf("Factorial of %d is %lld\n", number, fact);
    return 0;
}
