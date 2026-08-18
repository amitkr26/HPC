# 14 - Debugging

Debugging drills and the find-the-error content from every assignment,
gathered in one place.

## What already exists

| Source | Debugging content |
| --- | --- |
| Day-3 assignment (Lab-3) | Explain Q7 "Find the Error" (out-of-bounds `a[3]`), Explain Q8 "What is wrong" (`i <= 5` loop overflow), MCQ 1/4 (garbage, partial init) |
| Day-4 assignment (Lab-4) | Explain Q5 (string buffer overflow), Explain Q1 (missing `'\0'`) |
| `03-CHEAT-SHEET.md` | common compiler + runtime error tables |
| `03-ARRAYS/REVISION.md` | 10 find-the-error questions |
| `04-STRINGS/REVISION.md` | 10 find-the-error questions |

## The 5 big bugs so far

1. **Off-by-one loops** (`<= n`, `i = n` instead of `n-1`) - reads/writes past
   the array.
2. **Garbage values** - uninitialized local arrays/variables.
3. **scanf newline trap** - reading a char/line right after a number without
   flushing the buffer.
4. **`==` vs `=`** - assignment inside a condition (always true).
5. **String overflow** - `strcpy`/`strcat`/`%s` past the array size.

## How to practise

Every new day, add 1-2 real bugs to this module. Write the wrong program
first, run it, observe the failure, then fix and explain. See the template:
`TEMPLATES/Day-XX/DEBUGGING.md`.
