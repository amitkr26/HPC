#include<stdio.h>
int main()
{
    int a=5;
    int *ptr;
    ptr = &a;
    printf("%d\n", *ptr);
    printf("size of integer: %d", sizeof(int));

    return 0;
}