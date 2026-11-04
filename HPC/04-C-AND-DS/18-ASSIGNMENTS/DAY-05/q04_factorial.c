#include <stdio.h>

long factorial(int n);

int main() {
    int num;

    printf("Enter a number: ");
    scanf("%d", &num);

    printf("Factorial = %ld\n", factorial(num));

    return 0;
}

long factorial(int n) {
    int i;
    long f = 1;

    for (i = 1; i <= n; i++)
        f = f * i;

    return f;
}
