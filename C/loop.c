#include <stdio.h>

int main()
{
    int i = 6;

    do
    {
        printf("%d\n", i);
        ++i;
    }
    while(i <= 5);
    printf("%d\n", i);

    return 0;
}