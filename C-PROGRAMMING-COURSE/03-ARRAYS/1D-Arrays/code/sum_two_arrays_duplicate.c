#include <stdio.h>

int main()
{
    int a[5],b[5],sum[5], i;
    printf("Enter the elements of array 1: ");
    for(i=0;i<5;i++)
    {
        scanf("%d",&a[i]);
    }
    printf("1 array is:");

    for(int i = 0; i < 5; i++)
    {
        printf("%d ", a[i]);
    }

    printf("Enter the elements of array 2: ");
    for(i=0;i<5;i++)
    {
        scanf("%d",&b[i]);
    }
    printf("1 array is:");

    for(int i = 0; i < 5; i++)
    {
        printf("%d ", b[i]);
    }

    for(int i = 0; i < 5; i++)
    {
        sum[i] = a[i] + b[i];
    }
    printf("Sum of the arrays: ");

    for (i = 0; i < 5; i++)
    {
        printf("%d ", sum[i]);
    }

    return 0;
}