# Conditions

## What it is

`if`, `if-else`, `else-if` ladder, nested `if`, `switch`, and (later) the
ternary operator. `switch` works only for equality against integer/char
constants.

## Status

Completed (Day 2). Confidence 4/5. Ternary operator not started.

## Code

Simple if/else: `01-BEGINNER/Day-02/code/assignment/q01-q05`, `01-BEGINNER/Day-02/code/even_odd_check.c`,
`01-BEGINNER/Day-02/code/positive_negative_zero.c`
Else-if ladder: `01-BEGINNER/Day-02/code/assignment/grade_else_if.c`, `02-CORE-C/Conditions/code/grade_else_if_ladder*.c`
Nested if: `01-BEGINNER/Day-02/code/assignment/q06_max_of_three_nested_if.c`, `01-BEGINNER/Day-02/code/assignment/q07_leap_year_nested_if.c`,
`02-CORE-C/Conditions/code/leap_year.c`, `02-CORE-C/Conditions/code/salary_increment_nested_if.c`
Switch: `01-BEGINNER/Day-02/code/assignment/q08_calculator_switch.c`, `01-BEGINNER/Day-02/code/assignment/q09_vowel_or_consonant.c`,
`02-CORE-C/Conditions/code/calculator_switch*.c`, `02-CORE-C/Conditions/code/vowel_or_consonant.c`

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
