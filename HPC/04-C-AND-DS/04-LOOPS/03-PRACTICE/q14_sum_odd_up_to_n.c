/*
 * Question: Sum only odd numbers up to N.
 * Answer:   Input 5 -> Sum of odd numbers = 9  (1 + 3 + 5)
 *           Input 10 -> Sum of odd numbers = 25 (1 + 3 + 5 + 7 + 9)
 */
#include <stdio.h>

int main()
{
    int n, i, sum = 0;

    printf("Enter N: ");
    scanf("%d", &n);

    for(i = 1; i <= n; i++)
    {
        if(i % 2 != 0)
        {
            sum += i;
        }
    }

    printf("Sum of odd numbers up to %d = %d\n", n, sum);

    return 0;
}
