# Debugging: Pointers

## Common Errors

### 1. Dereferencing NULL pointer
```c
int *ptr = NULL;
*ptr = 10;  // CRASH! Segmentation fault
```
**Fix:** Always check `if(ptr != NULL)` before dereferencing.

### 2. Using uninitialized pointer
```c
int *ptr;       // contains garbage address
*ptr = 10;     // CRASH! Writing to random memory
```
**Fix:** Always initialize: `int *ptr = &variable;` or `int *ptr = NULL;`

### 3. Wrong pointer type
```c
float f = 3.14;
int *ptr = &f;  // Warning: type mismatch
printf("%d", *ptr);  // Wrong value
```
**Fix:** Use matching types: `float *ptr = &f;`

### 4. Dangling pointer
```c
int *ptr;
{
    int x = 10;
    ptr = &x;
}
printf("%d", *ptr);  // Undefined behavior! x is out of scope
```
**Fix:** Don't use pointer after the variable goes out of scope.

### 5. Memory leak with malloc
```c
int *ptr = (int*)malloc(sizeof(int));
ptr = NULL;  // Lost the address! Memory leak
```
**Fix:** Free before losing the pointer: `free(ptr); ptr = NULL;`

### 6. Pointer arithmetic overflow
```c
int arr[5] = {1,2,3,4,5};
int *ptr = arr;
printf("%d", *(ptr+10));  // Out of bounds!
```
**Fix:** Stay within array bounds.

### 7. Forgetting & in scanf
```c
int x;
scanf("%d", x);    // WRONG! Should be &x
scanf("%d", &x);   // Correct
```

## Debugging Tips
- Print pointer addresses with `%p` and cast to `(void*)`
- Use `*ptr` to check what a pointer points to
- Check for NULL before every dereference
- Use `valgrind` (Linux) to find memory errors
