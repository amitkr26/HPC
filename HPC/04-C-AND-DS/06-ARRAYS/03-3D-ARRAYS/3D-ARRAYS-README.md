# 3D Arrays

## Status

**Needs Practice** (Day 3). Print program + one real project done. Confidence 2/5.

## Code

- `03-ARRAYS/3D-Arrays/code/print_3d_array.c` - fixed 2x2x2 array, prints block by block
- `03-ARRAYS/3D-Arrays/code/three_d_array_marks.c` - **the multidimentional array assignment**:
  `marks[5][3][5]` = 5 departments x 3 students x 5 subjects; user selects a
  department, program prints each student's total and average (with 1-based to
  0-based index conversion)

## Theory (from Lab-3 MCQ 10, Explain Q5c)

- A 3D array is "an array of 2D arrays" - blocks/pages of 2D tables.
- Stored row-major too. Flat index for `a[i][j][k]` in `a[I][J][K]`:
  `i*(J*K) + j*K + k`.
- MCQ: `int arr[2][2][2] = {1,2,3,4,5,6,7,8};` -> `arr[1][0][1]` = flat index
  `1*4 + 0*2 + 1 = 5` -> value `6`.

## Practice targets

- Re-run `three_d_array_marks.c` for a different department from memory.
- Write a 2x2x2 program that lets the user fill all 8 values and prints them
  page by page (like the sample in the assignment PDF).
