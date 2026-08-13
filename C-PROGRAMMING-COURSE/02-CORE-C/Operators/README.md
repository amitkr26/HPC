# Operators

## What it is

Arithmetic `+ - * / %`, unary `+ - ++ --`, relational `> < >= <= == !=`,
logical `&& || !`, assignment `= += ...`, and the ternary `?:`.

## Status

Completed (Day 1) for arithmetic/unary. Increment/decrement expression
evaluation practised. Ternary operator not yet started.

## Code

- `C/Beginner/binary_arithmetic.c`, `C/Beginner/binary_arithmetic_input.c`
- `C/Beginner/unary_operators.c`
- `C/Intermediate/increment_decrement_operators.c`
- `C/Intermediate/increment_expression_eval1.c` (`z = x++ * --y`)
- `C/Intermediate/increment_expression_eval2.c` (`k = ++i * j--`)
- `C/Advanced/undefined_increment_behavior.c` - what NOT to write

## Key rules

- Pre-increment `++i`: increment first, then use.
- Post-increment `i++`: use first, then increment.
- `x++ * --y` evaluates with current `x` and pre-decremented `y`.
- Never write expressions that modify a variable twice in one expression
  (undefined behaviour).

## Dry run example (eval2)

`i=6, j=3`; `k = ++i * j--`:
1. `++i` -> `i=7`
2. `j--` uses `3`, then `j=2`
3. `k = 7 * 3 = 21`; output `7 2 21`
