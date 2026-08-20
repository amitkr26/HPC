#include <stdio.h>

int factorial(int n) {
    int i, result = 1;
    for(i = 2; i <= n; i++)
        result *= i;
    return result;
}

int main() {
    int num = 5;
    printf("Factorial of %d = %d\n", num, factorial(num));
    return 0;
}
