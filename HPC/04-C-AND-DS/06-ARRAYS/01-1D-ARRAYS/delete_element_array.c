#include <stdio.h>

int main()
{
    int arr[100];
    int n, i, value, position = -1;

    printf("Enter number of elements: ");
    scanf("%d", &n);

    printf("Enter array elements:\n");

    for (i = 0; i < n; i++)
    {
        scanf("%d", &arr[i]);
    }

    printf("Enter value to delete: ");
    scanf("%d", &value);

    // Search for the value
    for (i = 0; i < n; i++)
    {
        if (arr[i] == value)
        {
            position = i;
            break;
        }
    }

    // Delete the element
    if (position != -1)
    {
        for (i = position; i < n - 1; i++)
        {
            arr[i] = arr[i + 1];
        }

        n--;

        printf("Array after deletion:\n");

        for (i = 0; i < n; i++)
        {
            printf("%d ", arr[i]);
        }
    }
    else
    {
        printf("Value not found in array\n");
    }

    return 0;
}