# Examples: Functions

## Example 1: Simple Function
```c
#include <stdio.h>
int add(int a, int b) {
    return a + b;
}
int main() {
    int result = add(10, 20);
    printf("Sum = %d\n", result);
    return 0;
}
```

## Example 2: Call by Value vs Reference
```c
#include <stdio.h>
void swapByValue(int a, int b) {
    int temp = a;
    a = b;
    b = temp;
}
void swapByReference(int *a, int *b) {
    int temp = *a;
    *a = *b;
    *b = temp;
}
int main() {
    int x = 5, y = 10;
    swapByValue(x, y);
    printf("After swapByValue: x=%d, y=%d\n", x, y);
    swapByReference(&x, &y);
    printf("After swapByReference: x=%d, y=%d\n", x, y);
    return 0;
}
```

## Example 3: Recursive Factorial
```c
#include <stdio.h>
int factorial(int n) {
    if(n <= 1) return 1;
    return n * factorial(n - 1);
}
int main() {
    int num = 5;
    printf("Factorial of %d = %d\n", num, factorial(num));
    return 0;
}
```

## Example 4: Function returning multiple values
```c
#include <stdio.h>
void getMinMax(int arr[], int n, int *min, int *max) {
    int i;
    *min = *max = arr[0];
    for(i = 1; i < n; i++) {
        if(arr[i] < *min) *min = arr[i];
        if(arr[i] > *max) *max = arr[i];
    }
}
int main() {
    int arr[] = {23, 56, 11, 89, 45};
    int min, max;
    getMinMax(arr, 5, &min, &max);
    printf("Min: %d, Max: %d\n", min, max);
    return 0;
}
```

## Example 5: Static Variable
```c
#include <stdio.h>
void counter(void) {
    static int count = 0;
    count++;
    printf("Called %d times\n", count);
}
int main() {
    counter();  // Called 1 times
    counter();  // Called 2 times
    counter();  // Called 3 times
    return 0;
}
```
