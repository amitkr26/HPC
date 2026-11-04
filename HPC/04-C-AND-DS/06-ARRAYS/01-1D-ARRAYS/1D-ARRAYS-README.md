# 1D Arrays

Single-dimension arrays: the core of Day 3.

## Status

Completed (Day 3). Confidence 3-4/5.

## Code

| Topic | Program |
| --- | --- |
| Basics/init/input | `03-ARRAYS/1D-Arrays/code/total_average_marks.c`, `03-ARRAYS/Day-03/code/q01-q10` |
| Sum two arrays | `03-ARRAYS/1D-Arrays/code/sum_two_arrays.c` (+ `sum_two_arrays_duplicate.c` duplicate) |
| Total + average | `03-ARRAYS/1D-Arrays/code/total_average_marks.c` |
| Largest | `03-ARRAYS/1D-Arrays/code/largest_in_array.c`, `03-ARRAYS/Day-03/code/q03_largest_element.c` |
| Even/odd count | `03-ARRAYS/1D-Arrays/code/count_even_odd_array.c`, `03-ARRAYS/1D-Arrays/code/count_even_odd_ten_elements.c`, `03-ARRAYS/Day-03/code/q04_count_even_odd.c` |
| Reverse | `03-ARRAYS/1D-Arrays/code/reverse_array.c`, `03-ARRAYS/1D-Arrays/code/print_reverse_array.c`, `03-ARRAYS/Day-03/code/q05_reverse_array.c` |
| Copy | `03-ARRAYS/Day-03/code/q09_copy_array.c` |
| Compare identical | `03-ARRAYS/Day-03/code/q08_arrays_identical.c` |
| Swap first/last | `03-ARRAYS/Day-03/code/q07_swap_first_last.c` |
| Replace negatives | `03-ARRAYS/Day-03/code/q10_replace_negatives.c` |

## Key rules

- `int arr[100];` - fixed size known at compile time. Use `arr[n]` only with a
  variable-length array (VLA, C99) or a big fixed size + logical `n`.
- Length formula: `sizeof(arr)/sizeof(arr[0])` - works only where `arr` is a
  real array (not a function parameter/pointer).
- Valid indices `0 .. n-1`. Out of range = undefined behaviour.
- Partially initialized arrays are zero-filled; uninitialized locals hold
  garbage.

## Common mistakes

- Loop `i <= n` (off by one) -> reads/writes past the end.
- Deleting/inserting without shifting, or shifting the wrong direction.
- `scanf` without `&arr[i]`.
