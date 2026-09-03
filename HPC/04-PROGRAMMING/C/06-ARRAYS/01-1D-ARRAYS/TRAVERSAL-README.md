# Array Traversal

## What it is

Visiting every element of an array with a loop (usually `for`), either to read
it (input/output), or to inspect/change it.

## Status

Completed (Day 3). Confidence 4/5.

## Code

- `03-ARRAYS/1D-Arrays/code/print_reverse_array.c` - read N, print original then reversed
- `03-ARRAYS/2D-Arrays/code/print_2d_array.c` - nested loops over rows and columns
- `03-ARRAYS/3D-Arrays/code/print_3d_array.c` - triple nested loops
- Every `03-ARRAYS/Day-03/code/q*.c` program has an input loop and an output loop

## Key patterns

```c
/* input */
for (i = 0; i < n; i++) scanf("%d", &arr[i]);

/* output */
for (i = 0; i < n; i++) printf("%d ", arr[i]);

/* reverse traversal */
for (i = n - 1; i >= 0; i--) printf("%d ", arr[i]);
```

## Common mistakes

- Starting a reverse loop at `n` instead of `n-1` (reads one past the end).
- Using `<= n` in the forward loop.
- Forgetting `&` inside `scanf("%d", &arr[i])`.
