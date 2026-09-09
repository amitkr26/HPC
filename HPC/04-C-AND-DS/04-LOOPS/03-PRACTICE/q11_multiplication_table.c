/*
 * Question: Print the multiplication table of a number.
 * Answer:   Input 5 -> 5 x 1 = 5 ... 5 x 10 = 50
 */
#include <stdio.h>

int main()
{
    int num, i;

    printf("Enter a number: ");
    scanf("%d", &num);

    for(i = 1; i <= 10; i++)
    {
        printf("%d x %d = %d\n", num, i, num * i);
    }

    return 0;
}
