#include <stdio.h>

int main()
{
    int i,j,n;
    char ch = '*';
    printf("Enter no. of rows: ");
    scanf("%d", &n);
    for(i=1; i<=n; i++)
    {
        for(j=1;j<=n;j++)
        {
        printf("%c", ch);
        }
        printf("\n");
    }

    return 0;
}