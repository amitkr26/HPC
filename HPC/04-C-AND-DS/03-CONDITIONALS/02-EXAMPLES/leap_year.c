/*
 * Question: Write a C program to check whether a year is a leap year.
 * Answer:   A year is a leap year if (year % 400 == 0) or
 *           (year % 4 == 0 and year % 100 != 0).
 *           Input 2024 -> "2024 is a leap year"
 *           Input 2023 -> "2023 is not a leap year"
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