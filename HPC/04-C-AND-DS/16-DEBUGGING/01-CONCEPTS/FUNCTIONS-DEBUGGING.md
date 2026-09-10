# Debugging: Functions

## Common Errors

### 1. Missing function prototype
```c
#include <stdio.h>
int main() {
    add(5, 3);  // Warning: implicit declaration
}
int add(int a, int b) { return a+b; }
```
**Fix:** Add prototype before main: `int add(int, int);`

### 2. Return type mismatch
```c
int getFloat(void) {
    return 3.14;  // Warning: truncation
}
```
**Fix:** Use matching return type: `float getFloat(void)`

### 3. Forgetting return statement
```c
int add(int a, int b) {
    a + b;  // No return! Undefined behavior
}
```
**Fix:** `return a + b;`

### 4. Wrong number of arguments
```c
int add(int a, int b) { return a+b; }
add(1, 2, 3);  // Too many arguments
```

### 5. Modifying const parameters
```c
void func(const int x) {
    x = 10;  // Error! x is const
}
```

### 6. Infinite recursion (no base case)
```c
int factorial(int n) {
    return n * factorial(n-1);  // Never stops!
}
```
**Fix:** Always have a base case that stops recursion.

### 7. Stack overflow from deep recursion
```c
int recurse(int n) { return recurse(n+1); }  // Keeps calling
```
**Fix:** Ensure recursion terminates.

## Debugging Tips
- Add `printf` inside functions to trace execution
- Use a debugger to step through function calls
- Check return values match the declared type
- Verify argument count and types match the prototype
