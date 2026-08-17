# Debugging: Dynamic Memory

## Common Errors

### 1. Using malloc without checking NULL
```c
int *p = malloc(sizeof(int));
*p = 10;  // CRASH if malloc returned NULL
```
**Fix:** Always check: `if(p == NULL) { /* handle error */ }`

### 2. Memory leak
```c
void leak(void) {
    int *p = malloc(100);
    return;  // forgot free!
}
```
**Fix:** Always call `free(p)` before returning.

### 3. Double free
```c
int *p = malloc(sizeof(int));
free(p);
free(p);  // Error! Already freed
```
**Fix:** Set `p = NULL` after first free.

### 4. Using freed memory
```c
int *p = malloc(sizeof(int));
free(p);
*p = 10;  // Undefined behavior!
```

### 5. Wrong size calculation
```c
int *p = malloc(10);  // Only 10 bytes, not 10 ints!
```
**Fix:** `malloc(10 * sizeof(int))`

### 6. Forgetting to free in loops
```c
for(int i = 0; i < n; i++) {
    int *p = malloc(sizeof(int));
    // forgot free!
}
```

### 7. Freeing stack memory
```c
int x = 10;
free(&x);  // Error! Can't free stack memory
```

## Debugging Tips
- Use `valgrind` to detect leaks (Linux)
- Track malloc/free count
- Print addresses to verify allocation
- Set pointers to NULL after free
