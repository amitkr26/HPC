# Theory: Recursion

## What is Recursion?
Recursion is when a function calls itself to solve a problem.
Every recursive function must have:
1. **Base case** - when to stop
2. **Recursive case** - the function calls itself with a smaller/simpler input

## How Recursion Works
Each call creates a new stack frame:
```
factorial(3)
  factorial(2)
    factorial(1)
      return 1
    return 2 * 1 = 2
  return 3 * 2 = 6
```

## Types of Recursion

### Tail Recursion
Recursive call is the last operation:
```c
int factorial(int n, int acc) {
    if(n <= 1) return acc;
    return factorial(n-1, n*acc);  // last operation
}
```

### Head Recursion
Recursive call is the first operation:
```c
void print(int n) {
    if(n == 0) return;
    print(n-1);  // first operation
    printf("%d ", n);
}
```

### Direct Recursion
Function calls itself directly.

### Indirect Recursion
Function A calls Function B, which calls Function A.

## When to Use Recursion
- Tree traversal
- Divide and conquer algorithms
- Problems with recursive structure (factorial, Fibonacci)
- Backtracking problems

## When NOT to Use Recursion
- Simple loops can solve it better
- Performance is critical (recursion has overhead)
- Recursion depth may be too large

## Recursion vs Iteration
| Aspect | Recursion | Iteration |
|--------|-----------|-----------|
| Code | Often simpler | Sometimes complex |
| Memory | Uses stack | Uses less memory |
| Speed | Slower (function call overhead) | Faster |
| Debugging | Harder | Easier |
