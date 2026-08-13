# 1D Arrays

Single-dimension arrays: the core of Day 3.

## Status

Completed (Day 3). Confidence 3-4/5.

## Code

| Topic | Program |
| --- | --- |
| Basics/init/input | `C/Arrays/total_average_marks.c`, `C/Day3/q01-q10` |
| Sum two arrays | `C/Arrays/sum_two_arrays.c` (+ `sum_two_arrays_duplicate.c` duplicate) |
| Total + average | `C/Arrays/total_average_marks.c` |
| Largest | `C/Arrays/largest_in_array.c`, `C/Day3/q03_largest_element.c` |
| Even/odd count | `C/Arrays/count_even_odd_array.c`, `C/Arrays/count_even_odd_ten_elements.c`, `C/Day3/q04_count_even_odd.c` |
| Reverse | `C/Arrays/reverse_array.c`, `C/Arrays/print_reverse_array.c`, `C/Day3/q05_reverse_array.c` |
| Copy | `C/Day3/q09_copy_array.c` |
| Compare identical | `C/Day3/q08_arrays_identical.c` |
| Swap first/last | `C/Day3/q07_swap_first_last.c` |
| Replace negatives | `C/Day3/q10_replace_negatives.c` |

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
