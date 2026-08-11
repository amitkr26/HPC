/*
 * Question: Check if a number is positive or negative.
 * Answer:   Input 5  -> "The number 5 is positive."
 *           Input -3 -> "The number -3 is negative."
 *           Input 0  -> "The number 0 is neither positive nor negative."
 */
#include <stdio.h>

int main()
{
    int num;

    printf("Enter a number: ");
    scanf("%d", &num);

    if(num > 0)
    {
        printf("The number %d is positive.\n", num);
    }
    else if(num < 0)
    {
        printf("The number %d is negative.\n", num);
    }
    else
    {
        printf("The number 0 is neither positive nor negative.\n");
    }

    return 0;
}
