#include <stdio.h>
#include <stdlib.h>

int main()
{
    int n = 3;
    int *a;
    int *b;

    a = (int *)malloc(n * sizeof(int));

    for (int i = 0; i < n; i++)
    {
        a[i] = i + 1;
        printf("%d ", a[i]);
    }

    printf("\nBefore realloc:\n");

    for (int i = 0; i < n; i++)
    {
        printf("%d ", a[i]);
    }

    n = 5;

    b = (int *)realloc(a, n * sizeof(int));

    if (b == NULL)
    {
        printf("Memory allocation failed");
        free(a);
        return 1;
    }

    b[3] = 20;
    b[4] = 25;

    printf("\nAfter realloc:\n");

    for (int i = 0; i < n; i++)
    {
        printf("%d ", b[i]);
    }

    free(b);

    return 0;
}