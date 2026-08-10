#include <stdio.h>

int main()
{
    int num;

    printf("Enter a number: ");
    scanf("%d", &num);

    if(num>=18)
    {
        printf("%d is Adult\n", num);
    }
    else
    {
        printf("%d is Minor\n", num);
    }

    return 0;
}