/* Q8. Write a C program to input two arrays and check whether they
       are identical. */
#include <stdio.h>

int main()
{
    int a[100], b[100], n, i, identical = 1;

    printf("Enter number of elements: ");
    scanf("%d", &n);

    printf("Enter %d elements of first array:\n", n);
    for (i = 0; i < n; i++)
        scanf("%d", &a[i]);

    printf("Enter %d elements of second array:\n", n);
    for (i = 0; i < n; i++)
        scanf("%d", &b[i]);

    for (i = 0; i < n; i++)
    {
        if (a[i] != b[i])
        {
            identical = 0;
            break;
        }
    }

    if (identical == 1)
        printf("The arrays are identical\n");
    else
        printf("The arrays are not identical\n");

    return 0;
}
