#include <stdio.h>

int main() {
    int arr[5];
    int *ptr1 = arr;
    int *ptr2 = &arr[0];
    if(ptr1==ptr2){
        printf("Pointer to array and first element " "are equal");
    }
    else{
        printf("Pointer to array and first element" "are not equal");
    }
    return 0;
}