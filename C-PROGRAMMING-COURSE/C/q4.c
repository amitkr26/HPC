#include <stdio.h>
#include <stdlib.h>

int main()
{
    int *a =(int*)calloc(3, sizeof(int));

    if(a == NULL){
        printf("Memory allocation failed\n");
        return 1;
    }

    a[0]=5;
    a[1]=10;
    a[3]=15;

    a[2] = a[0] + a[1];

    printf("The sum of %d and %d is %d\n", a[0], a[1], a[2]);

    free(a);

    return 0;
}
