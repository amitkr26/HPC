# Input / Output

## What it is

`printf()` for output, `scanf()` for input. `&` gives the address a value must
be stored at. Format specifiers must match the variable type.

## Status

Completed (Day 1). Confidence 4/5.

## Code

- `01-BEGINNER/Day-01/code/hello_world.c` - first printf
- `01-BEGINNER/Day-01/code/print_variables.c` - printf with types
- `01-BEGINNER/Day-01/code/sum_of_two_numbers.c` - scanf two ints
- `01-BEGINNER/Day-01/code/binary_arithmetic_input.c` - scanf and arithmetic

## Key rules

- `scanf("%d", &num);` - the `&` is required for numeric/char variables.
- `scanf(" %c", &ch);` - leading space consumes the leftover newline.
- A string array name is already an address: `scanf("%s", name);` no `&`.

## Common mistakes

- Forgetting `&` in `scanf` -> crash or garbage.
- `scanf("%d\n", &n);` - `\n` in scanf causes trouble; never add it.
- Mixing up `%f`/`%lf` for float vs double.
- Not flushing leftover newline before reading a `char`.

## Practice target (missing Day-1 programs)

Simple interest, compound interest, BMI, Celsius/Fahrenheit, percentage,
discount, speed, net salary - they exist only in the Day-1 assignment docx.
Re-create them under `02-CORE-C/Input-Output/code/`.
