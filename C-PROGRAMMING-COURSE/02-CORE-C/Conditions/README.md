# Conditions

## What it is

`if`, `if-else`, `else-if` ladder, nested `if`, `switch`, and (later) the
ternary operator. `switch` works only for equality against integer/char
constants.

## Status

Completed (Day 2). Confidence 4/5. Ternary operator not started.

## Code

Simple if/else: `C/Day2/q01-q05`, `C/Beginner/even_odd_check.c`,
`C/Beginner/positive_negative_zero.c`
Else-if ladder: `C/Day2/grade_else_if.c`, `C/Intermediate/grade_else_if_ladder*.c`
Nested if: `C/Day2/q06_max_of_three_nested_if.c`, `C/Day2/q07_leap_year_nested_if.c`,
`C/Intermediate/leap_year.c`, `C/Intermediate/salary_increment_nested_if.c`
Switch: `C/Day2/q08_calculator_switch.c`, `C/Day2/q09_vowel_or_consonant.c`,
`C/Intermediate/calculator_switch*.c`, `C/Intermediate/vowel_or_consonant.c`

## Key rules

- `else` binds to the nearest unmatched `if`.
- Every `case` needs a `break` unless you want fall-through.
- Leap year: `(y%400==0) || (y%4==0 && y%100!=0)`.
- `switch` cannot test ranges, `>=`, floats, or combined conditions.

## Common mistakes

- `if(x = 5)` instead of `if(x == 5)` - assignment, always true.
- Missing `break` in switch -> accidental fall-through.
- Comparing a float with `==` (precision issues).

## Viva one-liners

- "Which is more flexible, switch or if-else?" -> if-else (ranges/conditions);
  switch can only compare equality against constants.
- "What must case labels be?" -> constant integer/char expressions.
