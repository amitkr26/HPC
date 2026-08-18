/*
 * Question: Write a C program to input two integers and apply the binary
 *           arithmetic operators +, -, *, / and %.
 * Answer:   Prints a+b, a*b, a/b and a%b (a-b is computed but never printed).
 *           Sample Input: 10 4
 *           Output: a+b is 14, a*b is 40, a/b is 2, a%b is 2
 */
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