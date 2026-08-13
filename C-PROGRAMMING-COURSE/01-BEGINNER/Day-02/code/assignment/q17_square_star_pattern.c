/*
 * Question: Print a square star (*) pattern of N rows using a for loop.
 * Answer:   Input 3 ->
 *           ***
 *           ***
 *           ***
 */
#include <stdio.h>

int main()
{
    int n, row, col;

    printf("Enter number of rows: ");
    scanf("%d", &n);

    for(row = 1; row <= n; row++)
    {
        for(col = 1; col <= n; col++)
        {
            printf("*");
        }
        printf("\n");
    }

    return 0;
}
