# Syntax: Functions

## Declaration
```c
return_type function_name(type1 param1, type2 param2);
```

## Definition
```c
return_type function_name(type1 param1, type2 param2) {
    // statements
    return value;  // if not void
}
```

## Call
```c
function_name(arg1, arg2);
result = function_name(arg1, arg2);
```

## void Function
```c
void printHello(void) {
    printf("Hello\n");
}
```

## Function with Array
```c
void printArray(int arr[], int n) {
    int i;
    for(i = 0; i < n; i++)
        printf("%d ", arr[i]);
}
```

## Recursive Function
```c
int factorial(int n) {
    if(n <= 1) return 1;     // base case
    return n * factorial(n-1); // recursive case
}
```

## Static Variable in Function
```c
void counter(void) {
    static int count = 0;  // initialized only once
    count++;
    printf("Count: %d\n", count);
}
```
