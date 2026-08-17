#include <stdio.h>
#include <stdlib.h>

int main()
{
    int *ptr;
    int n = 5, i;
    ptr = (int*)malloc(n * sizeof(int));
    // if(ptr == NULL){
    //     printf("Memory allocation failed\n");
    //     return 1;
    // }
    for(i = 0; i < n; i++){
        ptr[i] = i + 1;
    }
    printf("Using malloc:\n");
    for(i = 0; i < n; i++){
        printf("%d ", ptr[i]);
    }
    printf("\n");
    free(ptr);

    return 0;
}
