# Syntax: Pointers

## Declaration
```c
type *ptr;           // declare pointer
type *ptr = &var;    // declare and initialize
type *ptr = NULL;    // null pointer
```

## Assignment
```c
ptr = &variable;     // point to variable
ptr = array_name;    // point to first element
```

## Dereferencing
```c
*ptr                 // value at the address
*ptr = 100;          // change value through pointer
```

## Pointer Arithmetic
```c
ptr + n              // advance n elements
ptr - n              // go back n elements
ptr++                // next element
ptr--                // previous element
ptr1 - ptr2          // difference between pointers
```

## Comparison
```c
ptr1 == ptr2         // same address?
ptr == NULL          // is null?
ptr != NULL          // is not null?
```

## Function Parameters
```c
void func(int *ptr)          // accept pointer
func(&variable)              // pass address
func(array_name)             // pass array (decays to pointer)
```

## Common Patterns
```c
// Swap
void swap(int *a, int *b) { int t=*a; *a=*b; *b=t; }

// Return multiple values via pointers
void getMinMax(int arr[], int n, int *min, int *max) { ... }

// Dynamic allocation
int *ptr = (int*)malloc(n * sizeof(int));
```
