# C Programs

Practice programs written in C covering basic to intermediate concepts. The
programs are organized into **modules by programming level** and each file is
named after what it does. Every file begins with a header comment containing
the **Question** it solves and its **Answer** (with sample input/output where
applicable).

## Modules

```
C/
├── Beginner/       Basic I/O, variables, arithmetic, loops, simple if-else
├── Intermediate/   switch, nested if, increment/decrement, pointers
└── Advanced/       Complex expressions and undefined behaviour
```

## Module: Beginner

Programs that introduce I/O, variables, operators, loops and simple decision making.

| Program | Question | Answer / Output |
| --- | --- | --- |
| `hello_world.c` | Print "Hello" and "World". | `printf("Hello\n")` then `printf("World")`. |
| `print_variables.c` | Declare and print variables of different data types. | `%c`, `%d`, `%.2f`. Output: `name=R`, `age=25`, `marks=55.90`. |
| `sum_of_two_numbers.c` | Accept two numbers and print their sum. | Input `12 30` -> `The sum of your entered numbers is: 42`. |
| `binary_arithmetic.c` | Demonstrate binary arithmetic on fixed integers. | `a+b is 14`, `a*b is 40`, `a/b is 2`, `a%b is 2`. |
| `binary_arithmetic_input.c` | Apply `+ - * / %` to two user-input integers. | Same as `binary_arithmetic.c` with user input. |
| `unary_operators.c` | Demonstrate the unary `+` and `-` operators. | `+a` keeps sign, `-b` negates. |
| `swap_two_numbers.c` | Swap two numbers using a temporary variable. | Input `5 9` -> `9 5`. |
| `area_of_square.c` | Find the area of a square. | `area = side * side`. Input `5` -> `25.00`. |
| `area_of_circle.c` | Find the area of a circle. | `area = 3.14159 * r * r`. Input `5` -> `78.54`. |
| `circumference_of_circle.c` | Find the circumference of a circle. | `2 * PI * r`. Input `5` -> `31.42`. |
| `even_odd_check.c` | Check whether a number is even or odd. | `num % 2 == 0` -> Even. |
| `even_series.c` | Print all even numbers from 2 to 50. | Loop adds 2 each time. Output: `2, 4, ..., 50`. |
| `divisible_by_5.c` | Check whether a number is divisible by 5. | `num % 5 == 0`. |
| `hot_or_cold.c` | Print "hot" if number > 30, else "cold". | Input `35` -> hot; `20` -> cold. |
| `adult_or_minor.c` | Check whether a person is an adult or a minor. | `num >= 18` -> Adult. |
| `positive_negative_zero.c` | Check whether a number is positive, negative or zero. | `> 0` positive, `== 0` zero, else negative. |
| `do_while_demo.c` | Show how `do-while` differs from `while`. | Output: `6` then `7`. |
| `sum_of_odd_numbers.c` | Find the sum of all odd numbers from 1 to N. | Input `5` -> `Sum = 9`. |
| `multiplication_table.c` | Print the multiplication table of a number (1-10). | Input `5` -> `5 x 1 = 5` up to `5 x 10 = 50`. |
| `multiple_of_3_and_5.c` | Print numbers from 1 to 100 divisible by both 3 and 5. | Output: `15, 30, 45, 60, 75, 90`. |

## Module: Intermediate

Programs that use `switch`, nested `if-else`, increment/decrement operator
sequences, and pointers.

| Program | Question | Answer / Output |
| --- | --- | --- |
| `leap_year.c` | Check whether a year is a leap year. | `(year % 400 == 0) || (year % 4 == 0 && year % 100 != 0)`. |
| `leap_year_duplicate.c` | Check whether a year is a leap year. | Duplicate of `leap_year.c`. |
| `increment_decrement_operators.c` | Demonstrate pre/post increment and decrement. | From `c = 5`: `++c -> 6`, `--c -> 5`, `c-- prints 5`, `c++ prints 4`. |
| `calculator_switch_safe.c` | Simple calculator using `switch` (zero-safe). | Supports `+ - * /`. `10 + 4` -> `14`; `10 / 0` -> `Cannot divide by zero`. |
| `calculator_switch_basic.c` | Simple calculator using `switch`. | Supports `+ - * /`. Input `10 / 4` -> `Result = 2`. |
| `vowel_or_consonant.c` | Check vowel or consonant using `switch`. | Cases `a e i o u` -> vowel; default -> consonant. |
| `salary_increment_nested_if.c` | Nested if-else salary increment by age and salary. | `age >= 30`: 10% (<=500000) else 5%; else 8% (<=30000) else 3%. |
| `salary_increment_float.c` | Same salary logic using floating-point math. | Input `35 400000` -> new salary `440000.00`. |
| `pointer_sizeof_demo.c` | Demonstrate a pointer and `sizeof`. | `*ptr` prints `5`; `sizeof(int)` prints `4`. |
| `increment_expression_eval1.c` | Evaluate `z = x++ * --y` where `x = 10`, `y = 20`. | `11 19 190` (`z = 10 * 19`). |
| `increment_expression_eval2.c` | Evaluate `k = ++i * j--` where `i = 6`, `j = 3`. | `i = 7`, `j = 2`, `k = 21`. |

## Module: Advanced

Programs that combine operators in ways that rely on evaluation order or
trigger undefined behaviour.

| Program | Question | Answer / Output |
| --- | --- | --- |
| `undefined_increment_behavior.c` | Evaluate expressions mixing pre/post increments. | `7 12`; `11 19 190`; `6 30` (gcc 6.3.0; some lines are undefined behaviour). |
| `undefined_increment_behavior2.c` | Evaluate `q = ++p * p++` where `p = 4`. | Output (gcc 6.3.0): `6 30` (undefined behaviour). |

## Building

Compile any program with:

```bash
gcc <module>/<filename>.c -o <module>/<filename>
```

## Topic Map

- **Basic I/O and variables:** `hello_world.c`, `print_variables.c`, `sum_of_two_numbers.c`
- **Arithmetic operators:** `binary_arithmetic.c`, `binary_arithmetic_input.c`, `unary_operators.c`, `swap_two_numbers.c`
- **Geometry:** `area_of_square.c`, `area_of_circle.c`, `circumference_of_circle.c`
- **Decision making:** `even_odd_check.c`, `divisible_by_5.c`, `hot_or_cold.c`, `adult_or_minor.c`, `positive_negative_zero.c`, `leap_year.c`, `leap_year_duplicate.c`, `salary_increment_nested_if.c`, `salary_increment_float.c`
- **Loops:** `do_while_demo.c`, `even_series.c`, `sum_of_odd_numbers.c`, `multiplication_table.c`, `multiple_of_3_and_5.c`
- **Switch:** `calculator_switch_safe.c`, `calculator_switch_basic.c`, `vowel_or_consonant.c`
- **Increment/decrement operators:** `increment_decrement_operators.c`, `increment_expression_eval1.c`, `increment_expression_eval2.c`, `undefined_increment_behavior.c`, `undefined_increment_behavior2.c`
- **Pointers:** `pointer_sizeof_demo.c`
