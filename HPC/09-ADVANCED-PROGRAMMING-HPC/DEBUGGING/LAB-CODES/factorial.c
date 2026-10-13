// Lab 3: watchpoints and conditional breakpoints.
// Bug: int overflows for n >= 13 (13! = 6,227,020,800 > INT_MAX).
#include <stdio.h>

int factorial(int n) {
    int result = 1;
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

    int fact = factorial(number);
    printf("Factorial of %d is %d\n", number, fact);
    return 0;
}
