/*
 * Question: Write a C program that reads a number and prints "hot" if it is
 *           greater than 30, otherwise "cold".
 * Answer:   Input 35 -> "35 is hot"; Input 20 -> "20 is cold"
 */
#include <stdio.h>

int main()
{
    int num;

    printf("Enter a number: ");
    scanf("%d", &num);

    if(num>30)
    {
        printf("%d is hot\n", num);
    }
    else
    {
        printf("%d is cold\n", num);
    }

    return 0;
}