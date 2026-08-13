/* Q6. Delete a given value from an array. */
#include <stdio.h>

int main()
{
    int arr[100], n, i, value, position = -1;

    printf("Enter number of elements: ");
    scanf("%d", &n);

    printf("Enter %d elements:\n", n);
    for (i = 0; i < n; i++)
        scanf("%d", &arr[i]);

    printf("Enter the value to delete: ");
    scanf("%d", &value);

    for (i = 0; i < n; i++)
    {
        if (arr[i] == value)
        {
            position = i;
            break;
        }
    }

    if (position == -1)
    {
        printf("Value not found in array\n");
        return 1;
    }

    for (i = position; i < n - 1; i++)
        arr[i] = arr[i + 1];

    n--;

    printf("Array after deletion:\n");
    for (i = 0; i < n; i++)
        printf("%d ", arr[i]);
    printf("\n");

    return 0;
}
