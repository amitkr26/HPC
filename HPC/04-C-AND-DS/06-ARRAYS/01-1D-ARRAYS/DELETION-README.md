# Deletion

## What it is

Remove a value (or an index): find it, shift every element after it one step
left, and decrease the logical size. The trailing slot can be ignored.

## Status

Completed (Day 3). Confidence 3/5 (shift logic needs re-practice).

## Code

- `03-ARRAYS/Deletion/code/delete_element_array.c`
- `03-ARRAYS/Day-03/code/q06_delete_value.c`

## Key pattern

```c
/* find position */
for (i = 0; i < n; i++)
    if (arr[i] == value) { position = i; break; }

/* shift left */
for (i = position; i < n - 1; i++)
    arr[i] = arr[i + 1];
n--;
```

## Common mistakes

- Shifting only one element, or shifting to `n` instead of `n-1`.
- Forgetting to check the value exists before shifting.
- Keeping `n` unchanged so the "deleted" value still prints.

## Viva one-liner (from Lab-3 MCQ 6)

- Correct deletion: `for(int i = 2; i < size-1; i++) arr[i] = arr[i+1]; size--;`
  - `arr[2] = 0` leaves the slot, `arr[2] = arr[size-1]` reorders the array,
    and `free()` does not apply to stack arrays.
