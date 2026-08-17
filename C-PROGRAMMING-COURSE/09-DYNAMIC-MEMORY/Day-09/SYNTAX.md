# Syntax: Dynamic Memory

## Include Header
```c
#include <stdlib.h>
```

## malloc
```c
type *ptr = (type*)malloc(n * sizeof(type));
if(ptr == NULL) { /* error */ }
```

## calloc
```c
type *ptr = (type*)calloc(n, sizeof(type));
if(ptr == NULL) { /* error */ }
```

## realloc
```c
type *ptr = (type*)realloc(ptr, new_n * sizeof(type));
if(ptr == NULL) { /* error */ }
```

## free
```c
free(ptr);
ptr = NULL;
```

## Dynamic Array
```c
int n;
scanf("%d", &n);
int *arr = (int*)malloc(n * sizeof(int));
// use arr[0] to arr[n-1]
free(arr);
```

## Dynamic 2D Array
```c
int **mat = (int**)malloc(rows * sizeof(int*));
for(i = 0; i < rows; i++)
    mat[i] = (int*)malloc(cols * sizeof(int));
// use mat[i][j]
for(i = 0; i < rows; i++)
    free(mat[i]);
free(mat);
```

## Dynamic String
```c
char *s = (char*)malloc(100 * sizeof(char));
scanf("%99s", s);
free(s);
```
