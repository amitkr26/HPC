/*
 * Question: Write a C program to print all numbers from 1 to 100 that are
 *           divisible by both 3 and 5.
 * Answer:   i % 3 == 0 && i % 5 == 0 (i.e. multiples of 15).
 *           Output: 15, 30, 45, 60, 75, 90.
 */
#include <stdio.h>

int main()
{
    int i;

    for(i = 1; i <= 100; i++)
    {
        if(i % 3 == 0 && i % 5 == 0)
        {
            printf("%d\n", i);
        }
    }

    return 0;
}