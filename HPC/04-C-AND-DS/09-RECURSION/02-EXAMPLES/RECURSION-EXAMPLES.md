# Examples: Recursion

## Example 1: Factorial
```c
#include <stdio.h>
int factorial(int n) {
    if(n <= 1) return 1;
    return n * factorial(n - 1);
}
int main() {
    printf("5! = %d\n", factorial(5));  // 120
    return 0;
}
```

## Example 2: Fibonacci
```c
#include <stdio.h>
int fibonacci(int n) {
    if(n <= 1) return n;
    return fibonacci(n-1) + fibonacci(n-2);
}
int main() {
    int i;
    for(i = 0; i < 10; i++)
        printf("%d ", fibonacci(i));
    // 0 1 1 2 3 5 8 13 21 34
    return 0;
}
```

## Example 3: Power
```c
#include <stdio.h>
int power(int base, int exp) {
    if(exp == 0) return 1;
    return base * power(base, exp - 1);
}
int main() {
    printf("2^10 = %d\n", power(2, 10));  // 1024
    return 0;
}
```

## Example 4: Sum of Digits
```c
#include <stdio.h>
int digitSum(int n) {
    if(n == 0) return 0;
    return (n % 10) + digitSum(n / 10);
}
int main() {
    printf("Sum of 1234 = %d\n", digitSum(1234));  // 10
    return 0;
}
```

## Example 5: Reverse a String
```c
#include <stdio.h>
void reverse(char *s) {
    if(*s == '\0') return;
    reverse(s + 1);
    printf("%c", *s);
}
int main() {
    printf("Reverse of HELLO: ");
    reverse("HELLO");
    // OLLEH
    return 0;
}
```
