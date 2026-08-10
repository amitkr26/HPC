#include <stdio.h>

int main()
{
    int i = 6, j = 3, k;

    k = ++i * j--;

    printf("i = %d\n", i);
    printf("j = %d\n", j);
    printf("k = %d\n", k);

    return 0;
}