# Examples: Pointers

## Example 1: Pointer Basics
```c
#include <stdio.h>
int main() {
    int x = 10;
    int *ptr = &x;
    printf("Value of x: %d\n", x);
    printf("Address of x: %p\n", (void*)&x);
    printf("Value of ptr: %p\n", (void*)ptr);
    printf("Value at *ptr: %d\n", *ptr);
    return 0;
}
```

## Example 2: Swap Using Pointers
```c
#include <stdio.h>
void swap(int *a, int *b) {
    int temp = *a;
    *a = *b;
    *b = temp;
}
int main() {
    int x = 5, y = 10;
    printf("Before: x=%d, y=%d\n", x, y);
    swap(&x, &y);
    printf("After: x=%d, y=%d\n", x, y);
    return 0;
}
```

## Example 3: Pointer Arithmetic with Array
```c
#include <stdio.h>
int main() {
    int arr[] = {10, 20, 30, 40, 50};
    int *ptr = arr;
    int i;
    for(i = 0; i < 5; i++) {
        printf("arr[%d] = %d (address: %p)\n", i, *(ptr+i), (void*)(ptr+i));
    }
    return 0;
}
```

## Example 4: Double Pointer
```c
#include <stdio.h>
int main() {
    int x = 100;
    int *ptr = &x;
    int **pptr = &ptr;
    printf("x = %d\n", x);
    printf("*ptr = %d\n", *ptr);
    printf("**pptr = %d\n", **pptr);
    return 0;
}
```

## Example 5: Pointer to Find Largest
```c
#include <stdio.h>
int *findLargest(int *arr, int n) {
    int *largest = arr;
    int i;
    for(i = 1; i < n; i++) {
        if(*(arr+i) > *largest)
            largest = arr + i;
    }
    return largest;
}
int main() {
    int arr[] = {23, 56, 11, 89, 45};
    int *result = findLargest(arr, 5);
    printf("Largest: %d\n", *result);
    return 0;
}
```
