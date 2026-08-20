/*
 * Question: Write a C program to find the sum of all odd numbers from 1 to N.
 * Answer:   A for loop checks each number i from 1 to N and adds it to sum when
 *           i % 2 != 0.
 *           Sample Input: 5 -> Sum = 1 + 3 + 5 = 9
 */
#include <stdio.h>

int main()
{
    int i;
    int N, sum = 0;

    printf("Enter the number: ");
    scanf("%d", &N);

    for(i = 1; i <= N; i++)
    {
        if(i % 2 != 0)
        {
            sum = sum + i;
        }
    }

    printf("Sum = %d\n", sum);

    return 0;
}