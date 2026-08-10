#include <stdio.h>

int main() {
    int a, b, res;
    printf("Enter the value of a: ");
    scanf("%d", &a);
    printf("Enter the value of b: ");
    scanf("%d", &b);
    printf("a is %d and b is %d\n", a,b);
    res = a + b;
    printf("a+b is %d\n", res);
    res = a - b;
    res = a * b;
    printf("a*b is %d\n", res);
    res = a / b;
    printf("a/b is %d\n", res);
    res = a % b;
    printf("a%%b is %d\n", res);
    return 0;
}