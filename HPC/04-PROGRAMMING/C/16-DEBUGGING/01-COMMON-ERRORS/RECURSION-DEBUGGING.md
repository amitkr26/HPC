# Debugging: Recursion

## Common Errors

### 1. Missing base case
```c
int factorial(int n) {
    return n * factorial(n-1);  // Never stops!
}
```
**Fix:** Add base case: `if(n <= 1) return 1;`

### 2. Wrong base case
```c
int factorial(int n) {
    if(n == 0) return 0;  // Wrong! Should be 1
    return n * factorial(n-1);
}
```

### 3. Not making progress toward base case
```c
int func(int n) {
    if(n == 0) return 0;
    return func(n);  // Same n forever!
}
```
**Fix:** Ensure parameter moves toward base case: `func(n-1)`

### 4. Stack overflow
```c
int recurse(int n) { return recurse(n+1); }
```
**Fix:** Make sure recursion terminates.

### 5. Forgetting to return
```c
int factorial(int n) {
    if(n <= 1) return 1;
    n * factorial(n-1);  // No return!
}
```

## Debugging Tips
- Add printf before/after recursive call to trace
- Draw the call stack on paper
- Test with small inputs first
- Check base case is correct
- Verify progress toward base case
