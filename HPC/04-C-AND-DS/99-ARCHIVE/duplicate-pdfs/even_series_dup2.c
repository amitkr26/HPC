/*
 * Question: Write a C program to print all even numbers from 2 to 50.
 * Answer:   The loop starts at 2 and adds 2 each time, so i is always even.
 *           Output: 2, 4, 6, ..., 48, 50 (one per line).
 */
#include <stdio.h>

int main()
{
    int i;

    for(i = 2; i <= 50; i = i + 2)
    {
        printf("%d\n", i);
    }

    return 0;
}