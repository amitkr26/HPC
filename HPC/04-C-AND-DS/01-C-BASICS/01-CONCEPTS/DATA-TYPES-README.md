# Data Types

## What it is

The type of a value decides its size in memory, its range, and its format
specifier: `int` (%d), `float` (%f), `double` (%lf), `char` (%c).

## Status

Completed (Day 1). Confidence 3/5. `sizeof` touched via
`pointer_sizeof_demo.c`.

## Code

- `01-BEGINNER/Day-01/code/print_variables.c` - char/int/float together
- `05-POINTERS/code/pointer_sizeof_demo.c` - `sizeof(int)` = 4 bytes

## Theory

- Day-1 assignment (Explain Q14 float vs double, Q9 format specifiers)

## Quick reference

| Type | Size | Specifier |
| --- | --- | --- |
| int | 4 bytes | %d |
| float | 4 bytes | %f |
| double | 8 bytes | %lf |
| char | 1 byte | %c |

## Common mistakes

- Using `%d` with a `float`/`double` (garbage output).
- `printf("x=%f", x);` where `x` is `double` and you use `%f` - mismatch.
- Integer division: `7/2` is `3`, not `3.5` (use `7/2.0` or cast).
