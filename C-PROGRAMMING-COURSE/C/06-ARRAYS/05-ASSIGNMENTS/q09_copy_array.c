#include <stdio.h>

int main()
{
    int source[100], copy[100], n, i;

    printf("Enter number of elements: ");
    scanf("%d", &n);

    printf("Enter %d elements:\n", n);
    for (i = 0; i < n; i++)
        scanf("%d", &source[i]);

    for (i = 0; i < n; i++)
        copy[i] = source[i];

    printf("Elements of the copied array:\n");
    for (i = 0; i < n; i++)
        printf("%d ", copy[i]);
    printf("\n");

    return 0;
}