/*
 * Question: Write a C program to demonstrate the unary + and - operators.
 * Answer:   +a leaves the sign unchanged; -b negates the value of b.
 *           Sample Input: 3 -7 -> +a = 3 and -b = 7
 */
#include <stdio.h>

int main() {
    int a, b;
    printf("Enter the value of a and b: ");
    scanf("%d %d", &a, &b);
    printf("Your Entered number (a):%d -> Unary operation (+a):%d\n", a,+a);
    printf("Your Entered number (b):%d -> Unary operation (-b):%d\n", a,-b);

    return 0;
}