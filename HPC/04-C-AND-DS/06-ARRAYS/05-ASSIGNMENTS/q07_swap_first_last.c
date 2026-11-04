/* Q7. Write a C program to swap first and last elements in an array
       by getting user input. */
#include <stdio.h>

int main()
{
    int arr[100], n, i, temp;

    printf("Enter number of elements: ");
    scanf("%d", &n);

    printf("Enter %d elements:\n", n);
    for (i = 0; i < n; i++)
        scanf("%d", &arr[i]);

    printf("Original array:\n");
    for (i = 0; i < n; i++)
        printf("%d ", arr[i]);
    printf("\n");

    temp = arr[0];
    arr[0] = arr[n - 1];
    arr[n - 1] = temp;

    printf("Array after swapping first and last elements:\n");
    for (i = 0; i < n; i++)
        printf("%d ", arr[i]);
    printf("\n");

    return 0;
}
