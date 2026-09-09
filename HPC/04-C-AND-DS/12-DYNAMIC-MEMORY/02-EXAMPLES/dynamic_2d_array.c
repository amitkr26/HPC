#include <stdio.h>
#include <stdlib.h>

int main() {
    int rows, cols, i, j;
    printf("Enter rows and cols: ");
    scanf("%d %d", &rows, &cols);

    int **mat = (int**)malloc(rows * sizeof(int*));
    for(i = 0; i < rows; i++)
        mat[i] = (int*)malloc(cols * sizeof(int));

    for(i = 0; i < rows; i++)
        for(j = 0; j < cols; j++)
            mat[i][j] = i * cols + j + 1;

    printf("Matrix:\n");
    for(i = 0; i < rows; i++) {
        for(j = 0; j < cols; j++)
            printf("%3d ", mat[i][j]);
        printf("\n");
    }

    for(i = 0; i < rows; i++) free(mat[i]);
    free(mat);
    return 0;
}
