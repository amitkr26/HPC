/* Q2. Search for a given value in an array using linear search;
       print its index or "Not found". */
#include <stdio.h>

int main()
{
    int arr[100], n, i, value;
    int found = 0;

    printf("Enter number of elements: ");
    scanf("%d", &n);

    printf("Enter %d elements:\n", n);
    for (i = 0; i < n; i++)
        scanf("%d", &arr[i]);

    printf("Enter the value to search: ");
    scanf("%d", &value);

    for (i = 0; i < n; i++)
    {
        if (arr[i] == value)
        {
            printf("%d found at index %d\n", value, i);
            found = 1;
            break;
        }
    }

    if (found == 0)
        printf("Not found\n");

    return 0;
}
