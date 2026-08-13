# Loops

## What it is

`for` (known count), `while` (condition-first), `do-while` (body runs once,
condition at end). Nested loops build patterns. `break` exits, `continue`
skips to the next iteration.

## Status

Completed (Day 2). Confidence 4/5. `break`/`continue` practice still pending
(conceptual only so far).

## Code

For loops: `C/Day2/q10-q15`, `C/Beginner/even_series.c`,
`C/Beginner/sum_of_odd_numbers.c`, `C/Beginner/multiplication_table.c`
While: `C/Day2/q19_stars_row_while.c`, `C/Day2/q20_stars_row_while.c`
Do-while: `C/Beginner/do_while_demo.c`, `C/Beginner/stars_row_do_while.c`
Patterns: `C/Day2/q16_five_stars_row.c`, `q17_square_star_pattern.c`,
`q18_right_triangle_star.c`

## Key rules

- for: init; condition; update - all in one line.
- while: test BEFORE body; may run zero times.
- do-while: test AFTER body; runs at least once; ends with `;`.
- Right triangle: inner loop runs `1..row`, outer loop `1..n`.

## Common mistakes

- Off-by-one: `for(i=1; i<n; i++)` vs `i<=n`.
- Infinite loop: forgetting the increment/update.
- `do { } while (cond)` missing the trailing semicolon.
- Using `=` instead of `==` in the loop condition.

## Viva one-liners

- "When is for best?" -> known iteration count.
- "When while?" -> count not known ahead of time.
- "Which loop always runs at least once?" -> do-while (exit-controlled).
