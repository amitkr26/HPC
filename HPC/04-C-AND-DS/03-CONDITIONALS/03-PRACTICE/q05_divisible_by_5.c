/*
 * Question: Check if a number is divisible by 5.
 * Answer:   Input 25 -> "25 is divisible by 5."
 *           Input 27 -> "27 is not divisible by 5."
 */
#include <stdio.h>

int main()
{
    int num;

    printf("Enter a number: ");
    scanf("%d", &num);

    if(num % 5 == 0)
    {
        printf("%d is divisible by 5.\n", num);
    }
    else
    {
        printf("%d is not divisible by 5.\n", num);
    }

    return 0;
}
