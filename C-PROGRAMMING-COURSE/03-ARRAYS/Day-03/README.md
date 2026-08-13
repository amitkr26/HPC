# Day-03: Arrays

## Learning objectives

- Declare, initialize, and traverse 1D arrays.
- Insert, delete, search, reverse, copy, compare, and update array elements.
- Understand 2D/3D array layout and memory addressing.
- Explain bounds errors and garbage values.

## What I did today

- Studied: arrays from the Day-3 class assignment.
- Programs written: `C/Day3/q01-q10` (insert, linear search, largest,
  even/odd count, reverse, delete, swap first/last, identical, copy,
  replace negatives) - all with `.exe`, input files, and screenshots.
- Extra practice: `C/Arrays/` programs (2D/3D print, sum of arrays, largest,
  linear search, insert/delete, marks totals).
- Solved the 3D student-marks project:
  `C/Arrays/three_d_array_marks.c` (`Amit Kumar - multidimentional
  array-Assignment.pdf`).
- Assignment: `C/Assignmenmt/Amit_Kumar_Lab3_Day3_Assignment.docx` (solved:
  10 programs + 10 MCQs + 10 Explain answers).

## MCQs answered (Lab-3)

1. `int arr[5]={1,2,3}` -> `arr[4]` = c) 0 (partial init zero-fills)
2. Element count = b) `sizeof(arr)/sizeof(arr[0])`
3. `arr[2][1]` in 3x2 = b) 6
4. Uninitialized local arrays = c) garbage
5. Reverse loop output = b) `50 40 30 20 10`
6. Correct delete = b) shift-left loop + `size--`
7. Sum with `break` at i==2 = b) 30
8. Partially filled 2D = b) `0 0 0`
9. Self-overwrite reverse loop = b) `5 3 5`
10. 3D flat index `arr[1][0][1]` = b) 6

## Status

- Status: **Completed** (1D), **Needs Practice** (2D/3D/memory/bounds)
- Confidence: 3/5
- Gap to close: re-practice insertion/deletion shift logic; smallest element;
  sorting (not started).

Practice drills + the full Day-3 question set: `03-ARRAYS/PRACTICE.md`.
