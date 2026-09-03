/*
 * Question: Find the maximum of three numbers using Nested-if.
 * Answer:   Input 10 20 15 -> "Maximum = 20"
 */
#include <stdio.h>

int main()
{
    int a, b, c;

    printf("Enter three numbers: ");
    scanf("%d %d %d", &a, &b, &c);

    if(a > b)
    {
        if(a > c)
        {
            printf("Maximum = %d\n", a);
        }
        else
        {
            printf("Maximum = %d\n", c);
        }
    }
    else
    {
        if(b > c)
        {
            printf("Maximum = %d\n", b);
        }
        else
        {
            printf("Maximum = %d\n", c);
        }
    }

    return 0;
}
