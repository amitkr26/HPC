#include <stdio.h>
#include <stdlib.h>

int main() {
    int *ptr = (int*)malloc(sizeof(int));
    *ptr = 42;
    printf("Value: %d\n", *ptr);

    free(ptr);
    ptr = NULL;  // Good practice!

    // ptr is now NULL, safe to check
    if(ptr != NULL)
        printf("Value: %d\n", *ptr);
    else
        printf("Pointer is NULL after free\n");

    return 0;
}
