// Write a C program to print stars (*) in a row by getting user input using while loop.
#include <stdio.h>

int main()
{
    int n, i = 1;
    char ch = '*';

    printf("Enter number of stars: ");
    scanf("%d", &n);

    do
    {
        printf("%c", ch);
        i++;
    }
    while(i<=n);

    return 0;
}