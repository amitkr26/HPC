# Theory: Dynamic Memory Allocation

## Why Dynamic Memory?
- Array size must be known at compile time
- Dynamic memory allows size to be determined at runtime
- Useful when data size is unknown

## Stack vs Heap
| Aspect | Stack | Heap |
|--------|-------|------|
| Size | Limited | Large |
| Speed | Fast | Slower |
| Lifetime | Function scope | Until free() |
| Management | Automatic | Manual |

## malloc() - Memory Allocation
Allocates uninitialized memory:
```c
int *ptr = (int*)malloc(n * sizeof(int));
```
Returns NULL if allocation fails.

## calloc() - Contiguous Allocation
Allocates zero-initialized memory:
```c
int *ptr = (int*)calloc(n, sizeof(int));
```
All bytes set to 0.

## realloc() - Reallocate
Resizes previously allocated memory:
```c
ptr = (int*)realloc(ptr, new_size * sizeof(int));
```
May move to a new location.

## free() - Release Memory
Returns memory to the system:
```c
free(ptr);
ptr = NULL;  // good practice
```

## Memory Leak
Forgetting to free allocated memory:
```c
void leak(void) {
    int *p = malloc(100);
    // forgot to free!
}
```
Memory is lost until program ends.

## Common Patterns
```c
// Dynamic array
int *arr = (int*)malloc(n * sizeof(int));

// Dynamic 2D array
int **matrix = (int**)malloc(rows * sizeof(int*));
for(i = 0; i < rows; i++)
    matrix[i] = (int*)malloc(cols * sizeof(int));

// Dynamic structure
struct Student *s = malloc(sizeof(struct Student));

// Dynamic string
char *str = (char*)malloc(100 * sizeof(char));
```
