# Insertion

## What it is

Insert a new element at a given position: shift every element from the target
position one step right, put the new value in, and increase the logical size.

## Status

Completed (Day 3). Confidence 3/5 (shift logic needs re-practice).

## Code

- `C/Arrays/insert_element_array.c`
- `C/Day3/q01_insert_element.c`

## Key pattern

```c
for (i = n; i >= position; i--)   /* shift right, start at end */
{
    arr[i] = arr[i - 1];
}
arr[position - 1] = element;      /* 1-based position -> 0-based index */
n++;
```

## Common mistakes

- Shifting in the wrong direction (overwriting instead of shifting).
- Looping `i >= position` but forgetting the array needs one extra slot.
- Mixing up 1-based user position and 0-based index.

## Dry run

`arr = {10, 20, 30, 40, 50}`, insert `99` at position 3 (1-based):
1. Shift: `arr[5]=arr[4]=50`, `arr[4]=arr[3]=40`, `arr[3]=arr[2]=30`
2. Place: `arr[2]=99`
3. Result: `{10, 20, 99, 30, 40, 50}`, `n=6`
