/*
 * Question: Check if a number is even or odd.
 * Answer:   Input 8  -> "8 is even."
 *           Input 7  -> "7 is odd."
 */
#include <stdio.h>

int main()
{
    int num;

    printf("Enter a number: ");
    scanf("%d", &num);

    if(num % 2 == 0)
    {
        printf("%d is even.\n", num);
    }
    else
    {
        printf("%d is odd.\n", num);
    }

    return 0;
}
