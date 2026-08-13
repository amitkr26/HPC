/*
 * Question: Write a C program to check whether a year is a leap year.
 * Answer:   Same program as leap_year.c (duplicate copy). Uses the rule:
 *           (year % 400 == 0) || (year % 4 == 0 && year % 100 != 0).
 */
#include <stdio.h>

int main()
{
    int year;

    printf("Enter year: ");
    scanf("%d", &year);

    if((year % 400 == 0) || (year % 4 == 0 && year % 100 != 0))
    {
        printf("%d is a leap year\n", year);
    }
    else
    {
        printf("%d is not a leap year\n", year);
    }

    return 0;
}