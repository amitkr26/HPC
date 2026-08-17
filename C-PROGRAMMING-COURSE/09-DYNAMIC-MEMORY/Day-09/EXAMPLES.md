# Examples: Dynamic Memory

## Example 1: malloc
```c
#include <stdio.h>
#include <stdlib.h>
int main() {
    int n, i;
    printf("Enter size: ");
    scanf("%d", &n);
    int *arr = (int*)malloc(n * sizeof(int));
    if(arr == NULL) {
        printf("Memory allocation failed\n");
        return 1;
    }
    for(i = 0; i < n; i++)
        arr[i] = (i+1) * 10;
    for(i = 0; i < n; i++)
        printf("%d ", arr[i]);
    printf("\n");
    free(arr);
    return 0;
}
```

## Example 2: calloc
```c
#include <stdio.h>
#include <stdlib.h>
int main() {
    int n = 5, i;
    int *arr = (int*)calloc(n, sizeof(int));
    for(i = 0; i < n; i++)
        printf("%d ", arr[i]);  // all zeros
    printf("\n");
    free(arr);
    return 0;
}
```

## Example 3: realloc
```c
#include <stdio.h>
#include <stdlib.h>
int main() {
    int n = 3, i;
    int *arr = (int*)malloc(n * sizeof(int));
    for(i = 0; i < n; i++) arr[i] = i+1;
    n = 5;
    arr = (int*)realloc(arr, n * sizeof(int));
    for(i = 3; i < n; i++) arr[i] = i+1;
    for(i = 0; i < n; i++) printf("%d ", arr[i]);
    printf("\n");
    free(arr);
    return 0;
}
```

## Example 4: Dynamic Structure
```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
struct Student {
    int roll_no;
    char name[50];
    float marks;
};
int main() {
    struct Student *s = (struct Student*)malloc(sizeof(struct Student));
    s->roll_no = 1;
    strcpy(s->name, "Amit");
    s->marks = 85.5;
    printf("Roll: %d, Name: %s, Marks: %.1f\n",
           s->roll_no, s->name, s->marks);
    free(s);
    return 0;
}
```

## Example 5: Dynamic 2D Array
```c
#include <stdio.h>
#include <stdlib.h>
int main() {
    int rows = 3, cols = 4, i, j;
    int **mat = (int**)malloc(rows * sizeof(int*));
    for(i = 0; i < rows; i++)
        mat[i] = (int*)malloc(cols * sizeof(int));
    for(i = 0; i < rows; i++)
        for(j = 0; j < cols; j++)
            mat[i][j] = i * cols + j + 1;
    for(i = 0; i < rows; i++) {
        for(j = 0; j < cols; j++)
            printf("%3d ", mat[i][j]);
        printf("\n");
    }
    for(i = 0; i < rows; i++) free(mat[i]);
    free(mat);
    return 0;
}
```
