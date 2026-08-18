/*
 * Question: Write a C program to check whether a person is an adult or a minor.
 * Answer:   num >= 18 -> "Adult"; otherwise "Minor".
 *           Input 18 -> "18 is Adult"; Input 15 -> "15 is Minor"
 */
#include <stdio.h>

int main()
{
    int num;

    printf("Enter a number: ");
    scanf("%d", &num);

    if(num>=18)
    {
        printf("%d is Adult\n", num);
    }
    else
    {
        printf("%d is Minor\n", num);
    }

    return 0;
}