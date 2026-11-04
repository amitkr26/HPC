/*
 * Question: Print even numbers between 1 and 50.
 * Answer:   Output: 2 4 6 8 10 ... 46 48 50
 */
#include <stdio.h>

int main()
{
    int i;

    for(i = 2; i <= 50; i += 2)
    {
        printf("%d ", i);
    }
    printf("\n");

    return 0;
}
