/* Q10. Write a C program to replace every negative number in an array
        with 0 and display the updated array. */
#include <stdio.h>

int main()
{
    int arr[100], n, i;

    printf("Enter number of elements: ");
    scanf("%d", &n);

    printf("Enter %d elements:\n", n);
    for (i = 0; i < n; i++)
        scanf("%d", &arr[i]);

    printf("Original array:\n");
    for (i = 0; i < n; i++)
        printf("%d ", arr[i]);
    printf("\n");

    for (i = 0; i < n; i++)
    {
        if (arr[i] < 0)
            arr[i] = 0;
    }

    printf("Array after replacing negatives with 0:\n");
    for (i = 0; i < n; i++)
        printf("%d ", arr[i]);
    printf("\n");

    return 0;
}
