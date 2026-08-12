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
├── Arrays/         1D, 2D and 3D arrays, search, insert, delete
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
| `alphabets_a_to_z_duplicate.c` | Print alphabets `a` to `z`. | Duplicate of `Day2/q15`. |
| `five_stars_row_duplicate.c` | Print 5 stars in a row. | Duplicate of `Day2/q16`. |
| `square_star_pattern_duplicate.c` | Square star pattern of N rows. | Duplicate of `Day2/q17`. |
| `right_triangle_star_pattern_duplicate.c` | Right triangle star pattern. | Duplicate of `Day2/q18`. |
| `stars_row_do_while.c` | Print N stars in a row using `do-while`. | Input `5` -> `*****`. |
| `print_1_to_10_duplicate.c` | Print numbers from 1 to 10. | Duplicate of `Day2/q10`. |

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
| `grade_else_if_ladder.c` | Grade assignment using an else-if ladder. | Duplicate of `Day2/grade_else_if.c`. |
| `grade_else_if_ladder_variant.c` | Same grading logic with simpler bounds. | 90+ -> A; 75+ -> B; 50+ -> C; 35+ -> D; else Fail. |
| `max_of_three_nested_if_duplicate.c` | Maximum of three numbers using nested-if. | Duplicate of `Day2/q06`. |
| `atm_if_else.c` | ATM using only if...else. | Duplicate of `Day2/atm_simple.c`. |
| `atm_if_else_variant.c` | ATM simulation using integer balance. | PIN 1234 -> menu; else `Access Denied`. |

## Module: Arrays

Programs that store and manipulate collections of values using one-, two- and
three-dimensional arrays: display, sum, reverse, count, search, insert and
delete.

| Program | Question | Answer / Output |
| --- | --- | --- |
| `print_2d_array.c` | Print a fixed 2x3 two-dimensional array. | Rows `1 2 3` and `4 5 6`. |
| `print_3d_array.c` | Print a fixed 2x2x2 three-dimensional array. | Two blocks of 2 rows each. |
| `three_d_array_marks.c` | Store marks for 5 departments x 3 students x 5 subjects and show each student's total and average for a chosen department. | Input 1-5, 3 students, 5 subjects each. |
| `sum_two_arrays.c` | Add two arrays element-wise (size 5). | `sum[i] = arr1[i] + arr2[i]`. |
| `sum_two_arrays_duplicate.c` | Same as `sum_two_arrays.c`. | Duplicate. |
| `print_reverse_array.c` | Read N elements, print original and reversed array. | Uses a variable-length array. |
| `reverse_array.c` | Read N elements, print them in reverse order. | Loops from `n-1` down to `0`. |
| `count_even_odd_array.c` | Count even and odd elements in an array. | `N` element input. |
| `count_even_odd_ten_elements.c` | Count even and odd elements in an array of exactly 10. | Fixed 10 inputs. |
| `insert_element_array.c` | Insert an element at a given position. | Shifts elements right. |
| `delete_element_array.c` | Delete an element by value. | Shifts elements left. |
| `linear_search_array.c` | Search an array for a value. | Prints index or `Element not found`. |
| `largest_in_array.c` | Find the largest element in an array. | Scans the array for the maximum. |
| `total_average_marks.c` | Total and average of 5 subject marks. | `Average = total / 5.0`. |

## Module: Day2 (Lab 2 Assignment)

Twenty programming questions plus a grade program and a bonus ATM program
submitted for the Day-2 (Lab 2) assignment. Each file is named `qNN_<topic>.c`
matching the question number in the assignment sheet.

| Program | Question | Answer / Output |
| --- | --- | --- |
| `q01_positive_or_negative.c` | Check if a number is positive or negative. | `5` -> positive; `-3` -> negative; `0` -> neither. |
| `q02_even_or_odd.c` | Check if a number is even or odd. | `8` -> even; `7` -> odd. |
| `q03_adult_or_minor.c` | Check if a person is adult or minor (18). | `20` -> adult; `15` -> minor. |
| `q04_hot_or_cold.c` | Check if temperature is hot or cold (>= 30 Hot). | `35` -> Hot; `22` -> Cold. |
| `q05_divisible_by_5.c` | Check if a number is divisible by 5. | `25` -> divisible; `27` -> not. |
| `q06_max_of_three_nested_if.c` | Maximum of three numbers using nested-if. | `10 20 15` -> `Maximum = 20`. |
| `q07_leap_year_nested_if.c` | Leap year using nested-if. | `2024` leap; `1900` not; `2000` leap. |
| `q08_calculator_switch.c` | Calculator with switch-case (`+ - * /`). | `10 + 4` -> `14`; `/ 0` -> `Cannot divide by zero`. |
| `q09_vowel_or_consonant.c` | Vowel or consonant using switch. | `a` -> vowel; `b` -> consonant. |
| `q10_print_1_to_10.c` | Print numbers from 1 to 10. | `1 2 3 4 5 6 7 8 9 10`. |
| `q11_multiplication_table.c` | Multiplication table (1-10). | `5 x 1 = 5` ... `5 x 10 = 50`. |
| `q12_even_1_to_50.c` | Print even numbers between 1 and 50. | `2 4 6 ... 50`. |
| `q13_divisible_by_3_and_5.c` | Print numbers 1-100 divisible by both 3 and 5. | `15 30 45 60 75 90`. |
| `q14_sum_odd_up_to_n.c` | Sum only odd numbers up to N. | `N=5` -> `Sum = 9`. |
| `q15_alphabets_a_to_z.c` | Print alphabets a to z using a for loop. | `a b c ... z`. |
| `q16_five_stars_row.c` | Print 5 stars in a row using a for loop. | `*****`. |
| `q17_square_star_pattern.c` | Square star pattern of N rows. | `N=3` -> 3x3 block of stars. |
| `q18_right_triangle_star.c` | Right triangle star pattern. | `N=5` -> 1 star to 5 stars. |
| `q19_stars_row_while.c` | Stars in a row from user input, while loop. | `5` -> `*****`. |
| `q20_stars_row_while.c` | Stars in a row from user input, while loop. | Duplicate of Q19. `7` -> `*******`. |
| `grade_else_if.c` | Grade assignment using an else-if ladder. | 90-100 -> A; 75-89 -> B; 50-74 -> C; 35-49 -> D; <35 -> Fail. |
| `atm_simple.c` | Bonus: ATM using only if...else. | PIN 1234 -> menu; else `Access Denied`. |

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
- **Grades:** `grade_else_if_ladder.c`, `grade_else_if_ladder_variant.c`, `Day2/grade_else_if.c`
- **ATM:** `atm_if_else.c`, `atm_if_else_variant.c`, `Day2/atm_simple.c`
- **Increment/decrement operators:** `increment_decrement_operators.c`, `increment_expression_eval1.c`, `increment_expression_eval2.c`, `undefined_increment_behavior.c`, `undefined_increment_behavior2.c`
- **Pointers:** `pointer_sizeof_demo.c`
- **Arrays:** `print_2d_array.c`, `print_3d_array.c`, `three_d_array_marks.c`, `sum_two_arrays.c`, `sum_two_arrays_duplicate.c`, `print_reverse_array.c`, `reverse_array.c`, `count_even_odd_array.c`, `count_even_odd_ten_elements.c`, `insert_element_array.c`, `delete_element_array.c`, `linear_search_array.c`, `largest_in_array.c`, `total_average_marks.c`
