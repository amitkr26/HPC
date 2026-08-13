/*
 * Question: Write a C program to check whether a number is even or odd.
 * Answer:   num % 2 == 0 means the number is even.
 *           Input 8 -> "8 is Even"; Input 7 -> "7 is Odd"
 */
#include <stdio.h>

int main()
{
    int num;

    printf("Enter a number: ");
    scanf("%d", &num);

    if(num % 2 == 0)
    {
        printf("%d is Even\n", num);
    }
    else
    {
        printf("%d is Odd\n", num);
    }

    return 0;
}