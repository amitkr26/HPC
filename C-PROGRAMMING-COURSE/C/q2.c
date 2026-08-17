#include <stdio.h>
#include <stdlib.h>

int main()
{
    int *a, *b;

    a = (int*)malloc(sizeof(int));
    b = (int*)malloc(sizeof(int));

    if(a == NULL || b == NULL){
        printf("Memory allocation failed\n");
        return 1;
    }

    printf("Enter a value for a:");
    scanf("%d", &a);

    printf("Enter a value for b:");
    scanf("%d", &b);

    printf("You Entered:\n");
    printf("Value of a:%d\n",a);
    printf("Value of b:%d\n",b);

    free(a);
    free(b);
    
    return 0;
}
