#include <stdio.h>

int main() {
    int arr[5] = {10, 20, 30, 40, 50};
    int *p;

    p = &arr[0];

    printf("Address of arr[0]  (p)   = %p\n", (void*)p);
    printf("Address of arr[1]  (p+1) = %p\n", (void*)(p + 1));
    printf("Address of arr[2]  (p+2) = %p\n", (void*)(p + 2));
    printf("Predicted address of p+3 (arr[3]) = %p\n", (void*)(p + 3));
    printf("Verified address of arr[3] using &arr[3] = %p\n", (void*)&arr[3]);

    return 0;
}
