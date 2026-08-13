# Searching (Linear Search)

## What it is

Scan the array from the first element, comparing each with the target value.
Stop at the first match; if the whole array is scanned with no match, the
value is not present.

## Status

Completed (Day 3). Confidence 4/5.

## Code

- `C/Arrays/linear_search_array.c`
- `C/Day3/q02_linear_search.c`

## Key pattern

```c
int found = 0;
for (i = 0; i < n; i++)
{
    if (arr[i] == value)
    {
        printf("Found at index %d\n", i);
        found = 1;
        break;
    }
}
if (found == 0) printf("Element not found\n");
```

## Common mistakes

- Forgetting the `found` flag and printing "not found" even after a match.
- Breaking out of the loop but then continuing anyway.

## Viva one-liner

- "What is the worst case?" -> target at the last index or absent: n comparisons.
