/*
 * Question: Print only numbers divisible by both 3 and 5 between 1 and 100.
 * Answer:   Output: 15 30 45 60 75 90
 */
#include <stdio.h>

int main()
{
    int i;

    for(i = 1; i <= 100; i++)
    {
        if(i % 3 == 0 && i % 5 == 0)
        {
            printf("%d ", i);
        }
    }
    printf("\n");

    return 0;
}
