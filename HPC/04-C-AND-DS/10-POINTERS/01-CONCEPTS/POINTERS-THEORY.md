# Theory: Pointers

## What is a Pointer?
A pointer is a variable that stores the memory address of another variable.
Instead of holding a value directly, it "points to" where the value is stored in memory.

## Why Use Pointers?
1. **Efficiency** - Pass large data without copying
2. **Flexibility** - Modify variables in other functions
3. **Dynamic memory** - Allocate memory at runtime
4. **Data structures** - Build linked lists, trees, graphs

## Memory Address
Every variable in memory has:
- An **address** (where it is stored)
- A **value** (what it holds)
- A **type** (what kind of data)

Example:
```c
int x = 10;
// x is stored at address 0x7ffd5e8a (example)
// x holds the value 10
```

## Pointer Declaration
```c
int *ptr;      // pointer to int
float *fptr;   // pointer to float
char *cptr;    // pointer to char
```

The `*` indicates this is a pointer variable.

## Address-Of Operator (&)
```c
int x = 10;
int *ptr = &x;  // ptr now holds the address of x
```

## Dereference Operator (*)
```c
int x = 10;
int *ptr = &x;
printf("%d", *ptr);  // prints 10 (value at the address)
```

## NULL Pointer
```c
int *ptr = NULL;  // points to nothing
```
Always check before dereferencing:
```c
if(ptr != NULL) {
    printf("%d", *ptr);
}
```

## Pointer Arithmetic
```c
int arr[] = {10, 20, 30};
int *ptr = arr;     // points to arr[0]
printf("%d", *ptr);     // 10
printf("%d", *(ptr+1)); // 20
printf("%d", *(ptr+2)); // 30
```

## Pointers and Arrays
Array name is a constant pointer to the first element:
```c
int arr[5] = {1,2,3,4,5};
int *ptr = arr;  // same as &arr[0]
// arr[i] is equivalent to *(arr+i) or *(ptr+i)
```

## Double Pointers
A pointer that stores the address of another pointer:
```c
int x = 10;
int *ptr = &x;
int **pptr = &ptr;  // pointer to pointer
printf("%d", **pptr);  // prints 10
```

## Pass by Reference
Using pointers to modify variables in functions:
```c
void swap(int *a, int *b) {
    int temp = *a;
    *a = *b;
    *b = temp;
}
int main() {
    int x = 5, y = 10;
    swap(&x, &y);  // pass addresses
    // x=10, y=5
}
```
