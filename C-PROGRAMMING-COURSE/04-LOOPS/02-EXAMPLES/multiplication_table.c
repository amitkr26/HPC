/*
 * Question: Write a C program to print the multiplication table of a number
 *           entered by the user (from 1 to 10).
 * Answer:   A for loop from 1 to 10 prints "num x i = num * i".
 *           Sample Input: 5 -> prints 5 x 1 = 5 up to 5 x 10 = 50.
 */
#include <stdio.h>

int main()
{
    int i, num;

    printf("Enter the number: ");
    scanf("%d", &num);

    for(i = 1; i <= 10; i++)
    {
        printf("%d x %d = %d\n", num, i, num * i);
    }

    return 0;
}