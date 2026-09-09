/*
 * Question: Write a C program to demonstrate the binary arithmetic operators on
 *           two fixed integers a = 10 and b = 4.
 * Answer:   Output: a+b is 14, a*b is 40, a/b is 2, a%b is 2
 *           (a-b is computed but never printed).
 */
#include <stdio.h>

int main() {
    int a=10, b=4, res;
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