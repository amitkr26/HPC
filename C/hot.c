#include <stdio.h>

int main()
{
    int num;

    printf("Enter a number: ");
    scanf("%d", &num);

    if(num>30)
    {
        printf("%d is hot\n", num);
    }
    else
    {
        printf("%d is cold\n", num);
    }

    return 0;
}