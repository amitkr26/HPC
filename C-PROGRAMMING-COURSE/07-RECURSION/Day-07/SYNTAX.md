# Syntax: Recursion

## Basic Structure
```c
return_type function(params) {
    if(base_case) {
        return base_value;
    }
    return function(smaller_params);  // recursive call
}
```

## Factorial
```c
int factorial(int n) {
    if(n <= 1) return 1;
    return n * factorial(n - 1);
}
```

## Fibonacci
```c
int fibonacci(int n) {
    if(n <= 1) return n;
    return fibonacci(n-1) + fibonacci(n-2);
}
```

## Sum of Digits
```c
int digitSum(int n) {
    if(n == 0) return 0;
    return (n % 10) + digitSum(n / 10);
}
```

## Power
```c
int power(int base, int exp) {
    if(exp == 0) return 1;
    return base * power(base, exp - 1);
}
```

## Array Sum
```c
int arrSum(int arr[], int n) {
    if(n == 0) return 0;
    return arr[n-1] + arrSum(arr, n-1);
}
```

## String Length
```c
int strLen(char *s) {
    if(*s == '\0') return 0;
    return 1 + strLen(s + 1);
}
```
