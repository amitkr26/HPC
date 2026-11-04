/*
 * Question: Write a C program to swap two numbers using a temporary variable.
 * Answer:   temp = num1; num1 = num2; num2 = temp.
 *           Sample Input: 5 9 -> Output: "The numbers are: 9 5"
 */
#include <stdio.h>

#define PI 3.14159

int main() {
    int num1, num2, temp;
    printf("Enter two numbers:");
    scanf("%d %d", &num1, &num2);
    printf("The numbers are: %d %d\n", num1, num2);
    temp = num1;
    num1 = num2;
    num2 = temp;

    printf("The numbers are: %d %d", num1, num2);
    return 0;
}