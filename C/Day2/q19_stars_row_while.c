/*
 * Question: Print stars (*) in a row by getting user input using a while loop.
 * Answer:   Input 5 -> *****
 */
#include <stdio.h>

int main()
{
    int n, i = 0;

    printf("Enter number of stars: ");
    scanf("%d", &n);

    while(i < n)
    {
        printf("*");
        i++;
    }
    printf("\n");

    return 0;
}
