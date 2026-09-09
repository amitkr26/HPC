/*
 * Question: Find the Leap Year using Nested-if.
 * Answer:   A year is a leap year if it is divisible by 4,
 *           except century years, which must be divisible by 400.
 *           Input 2024 -> "2024 is a leap year."
 *           Input 1900 -> "1900 is not a leap year."
 *           Input 2000 -> "2000 is a leap year."
 */
#include <stdio.h>

int main()
{
    int year;

    printf("Enter a year: ");
    scanf("%d", &year);

    if(year % 4 == 0)
    {
        if(year % 100 == 0)
        {
            if(year % 400 == 0)
            {
                printf("%d is a leap year.\n", year);
            }
            else
            {
                printf("%d is not a leap year.\n", year);
            }
        }
        else
        {
            printf("%d is a leap year.\n", year);
        }
    }
    else
    {
        printf("%d is not a leap year.\n", year);
    }

    return 0;
}
