# 2D Arrays

## Status

**Needs Practice** (Day 3). Only one print program + MCQs + memory theory so
far. Confidence 2/5.

## Code

- `03-ARRAYS/2D-Arrays/code/print_2d_array.c` - fixed 2x3 array, row-wise output

## Theory (from Lab-3 Explain Q3-Q4, MCQ 3/8)

- Stored **row-major**: entire first row, then second, etc., in one contiguous
  block.
- Element address: `base + (i * number_of_columns + j) * sizeof(element)`.
- Declaration: `int b[2][3] = {{1,2,3},{4,5,6}};`
- Partial rows zero-fill: `int a[3][3]={{1,2},{3},{4,5,6}};` ->
  `a[0][2]`, `a[1][1]`, `a[1][2]` are 0.

## Practice targets

- Write a program that reads a 3x3 matrix from the user and prints it as a grid.
- Add two 3x3 matrices (element-wise) and print the result.
- Find the row with the largest sum.
- Transpose a matrix (swap rows and columns).
