#include <stdio.h>

int main()
{
    int marks[5];
    int total = 0;
    float average;
    printf("Enter marks of 5 subjects:\n");
    for(int i = 0; i < 5; i++)
    {
        scanf("%d", &marks[i]);
    }

    for(int i = 0; i < 5; i++)
    {
        total = total + marks[i];
    }

    average = (float)total / 5;

    printf("Total = %d\n", total);
    printf("Average = %.2f\n", average);

    return 0;
}