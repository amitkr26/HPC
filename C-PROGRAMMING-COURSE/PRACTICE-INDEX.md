# Practice Index - Every Instructor Question and Program

This is the master map of ALL practice material given by the instructor,
together with the programs written for it. Every program that exists in the
workspace is listed below by its real path in `C/`. Use this index to see what
practice exists, where the code lives, and what is still missing.

Paths are relative to the workspace root.

- **Question source** = the assignment sheet that contains the question.
- **Solved as** = the `.c` program (real path in `C/`).
- **Status** = `[x]` done / `[~]` duplicate, extra, or partial / `[ ]` not written.

---

## Day 1 - Fundamentals (20 lab questions)

Question source: `C/Assignmenmt/Amit_Kumar_CDay1_Assignment.docx`

| # | Question (short) | Solved as | Status |
| --- | --- | --- | --- |
| 1 | Declare two int variables, assign, display | `01-BEGINNER/Day-01/code/print_variables.c` | [x] |
| 2 | Input name, print "Welcome NAME to C Programming" | (not written) | [ ] |
| 3 | First name, last name, age with proper names | (not written) | [ ] |
| 4 | Area of square (input side) | `01-BEGINNER/Day-01/code/area_of_square.c` | [x] |
| 5 | Constant pi, circumference of circle | `01-BEGINNER/Day-01/code/circumference_of_circle.c` | [x] |
| 6 | Area of circle (input radius) | `01-BEGINNER/Day-01/code/area_of_circle.c` | [x] |
| 7 | Swap two numbers | `01-BEGINNER/Day-01/code/swap_two_numbers.c` | [x] |
| 8 | Two ints: + - * / (float) % | `01-BEGINNER/Day-01/code/binary_arithmetic_input.c` | [x] |
| 9 | Simple Interest | (not written) | [ ] |
| 10 | Add, subtract, multiply, divide two numbers | `01-BEGINNER/Day-01/code/binary_arithmetic.c`, `02-CORE-C/Conditions/code/calculator_switch_basic.c` | [~] |
| 11 | Compound Interest | (not written) | [ ] |
| 12 | BMI | (not written) | [ ] |
| 13 | Celsius to Fahrenheit | (not written) | [ ] |
| 14 | Fahrenheit to Celsius | (not written) | [ ] |
| 15 | Percentage of marks (5 subjects) | `03-ARRAYS/1D-Arrays/code/total_average_marks.c` | [~] |
| 16 | Discounted price | (not written) | [ ] |
| 17 | Speed = distance / time | (not written) | [ ] |
| 18 | Net salary = basic + allowance - deductions | `02-CORE-C/Conditions/code/salary_increment_float.c`, `02-CORE-C/Conditions/code/salary_increment_nested_if.c` | [~] |
| 19 | Predict output: `x++` / `++x` sequence | `02-CORE-C/Operators/code/increment_decrement_operators.c` | [x] |
| 20 | Predict output: `k = ++i * j--` | `02-CORE-C/Operators/code/increment_expression_eval2.c`, `12-ADVANCED-C/code/undefined_increment_behavior.c` | [x] |

Missing programs (Q2, Q3, Q9, Q11-Q14, Q16, Q17): practice targets - write them.

## Day 2 - Conditions, Loops, Patterns (20 lab questions + bonus)

Question source: `C/Assignmenmt/Amit_Kumar_Lab2_Day2_Assignment.pdf`
(solved, with markdown copy at `01-BEGINNER/Day-02/PRACTICE.md`).

| # | Question (short) | Solved as | Status |
| --- | --- | --- | --- |
| 1 | Positive or negative | `01-BEGINNER/Day-02/code/assignment/q01_positive_or_negative.c` | [x] |
| 2 | Even or odd | `01-BEGINNER/Day-02/code/assignment/q02_even_or_odd.c` | [x] |
| 3 | Adult or minor (18) | `01-BEGINNER/Day-02/code/assignment/q03_adult_or_minor.c` | [x] |
| 4 | Hot or cold (>= 30) | `01-BEGINNER/Day-02/code/assignment/q04_hot_or_cold.c` | [x] |
| 5 | Divisible by 5 | `01-BEGINNER/Day-02/code/assignment/q05_divisible_by_5.c` | [x] |
| 6 | Maximum of three (nested if) | `01-BEGINNER/Day-02/code/assignment/q06_max_of_three_nested_if.c`, `02-CORE-C/Conditions/code/max_of_three_nested_if_duplicate.c` | [x] |
| 7 | Leap year (nested if) | `01-BEGINNER/Day-02/code/assignment/q07_leap_year_nested_if.c`, `02-CORE-C/Conditions/code/leap_year.c` | [x] |
| 8 | Calculator with switch | `01-BEGINNER/Day-02/code/assignment/q08_calculator_switch.c`, `02-CORE-C/Conditions/code/calculator_switch_safe.c` | [x] |
| 9 | Vowel or consonant (switch) | `01-BEGINNER/Day-02/code/assignment/q09_vowel_or_consonant.c`, `02-CORE-C/Conditions/code/vowel_or_consonant.c` | [x] |
| 10 | Print 1 to 10 | `01-BEGINNER/Day-02/code/assignment/q10_print_1_to_10.c`, `01-BEGINNER/Day-02/code/assignment/q10_print_1_to_10.c` | [x] |
| 11 | Multiplication table (1-10) | `01-BEGINNER/Day-02/code/assignment/q11_multiplication_table.c`, `01-BEGINNER/Day-02/code/multiplication_table.c` | [x] |
| 12 | Even numbers 1 to 50 | `01-BEGINNER/Day-02/code/assignment/q12_even_1_to_50.c`, `01-BEGINNER/Day-02/code/even_series.c` | [x] |
| 13 | Numbers 1-100 divisible by 3 and 5 | `01-BEGINNER/Day-02/code/assignment/q13_divisible_by_3_and_5.c`, `01-BEGINNER/Day-02/code/multiple_of_3_and_5.c` | [x] |
| 14 | Sum of odd numbers up to N | `01-BEGINNER/Day-02/code/assignment/q14_sum_odd_up_to_n.c`, `01-BEGINNER/Day-02/code/sum_of_odd_numbers.c` | [x] |
| 15 | Alphabets a to z | `01-BEGINNER/Day-02/code/assignment/q15_alphabets_a_to_z.c`, `01-BEGINNER/Day-02/code/assignment/q15_alphabets_a_to_z.c` | [x] |
| 16 | Five stars in a row | `01-BEGINNER/Day-02/code/assignment/q16_five_stars_row.c`, `01-BEGINNER/Day-02/code/assignment/q16_five_stars_row.c` | [x] |
| 17 | Square star pattern (N rows) | `01-BEGINNER/Day-02/code/assignment/q17_square_star_pattern.c`, `01-BEGINNER/Day-02/code/assignment/q17_square_star_pattern.c` | [x] |
| 18 | Right triangle star pattern | `01-BEGINNER/Day-02/code/assignment/q18_right_triangle_star.c`, `01-BEGINNER/Day-02/code/assignment/q18_right_triangle_star.c` | [x] |
| 19 | Stars in a row (while) | `01-BEGINNER/Day-02/code/assignment/q19_stars_row_while.c` | [x] |
| 20 | Stars in a row (while) | `01-BEGINNER/Day-02/code/assignment/q20_stars_row_while.c` (duplicate of Q19) | [~] |
| Bonus | Grade with else-if ladder | `01-BEGINNER/Day-02/code/assignment/grade_else_if.c`, `02-CORE-C/Conditions/code/grade_else_if_ladder.c`, `02-CORE-C/Conditions/code/grade_else_if_ladder_variant.c` | [x] |
| Bonus | ATM (if-else only) | `01-BEGINNER/Day-02/code/assignment/atm_simple.c`, `02-CORE-C/Conditions/code/atm_if_else.c`, `02-CORE-C/Conditions/code/atm_if_else_variant.c` | [x] |

## Day 3 - Arrays (10 lab questions)

Question source: `C/Assignmenmt/Amit_Kumar_Lab3_Day3_Assignment.docx`
(solved; source programs in `03-ARRAYS/Day-03/code/`).

| # | Question | Solved as | Status |
| --- | --- | --- | --- |
| 1 | Insert an element at a position | `03-ARRAYS/Day-03/code/q01_insert_element.c`, `03-ARRAYS/Insertion/code/insert_element_array.c` | [x] |
| 2 | Linear search | `03-ARRAYS/Day-03/code/q02_linear_search.c`, `03-ARRAYS/Searching/code/linear_search_array.c` | [x] |
| 3 | Largest element | `03-ARRAYS/Day-03/code/q03_largest_element.c`, `03-ARRAYS/1D-Arrays/code/largest_in_array.c` | [x] |
| 4 | Count even and odd | `03-ARRAYS/Day-03/code/q04_count_even_odd.c`, `03-ARRAYS/1D-Arrays/code/count_even_odd_array.c`, `03-ARRAYS/1D-Arrays/code/count_even_odd_ten_elements.c` | [x] |
| 5 | Reverse an array | `03-ARRAYS/Day-03/code/q05_reverse_array.c`, `03-ARRAYS/1D-Arrays/code/reverse_array.c`, `03-ARRAYS/1D-Arrays/code/print_reverse_array.c` | [x] |
| 6 | Delete a value | `03-ARRAYS/Day-03/code/q06_delete_value.c`, `03-ARRAYS/Deletion/code/delete_element_array.c` | [x] |
| 7 | Swap first and last | `03-ARRAYS/Day-03/code/q07_swap_first_last.c` | [x] |
| 8 | Two arrays identical | `03-ARRAYS/Day-03/code/q08_arrays_identical.c` | [x] |
| 9 | Copy one array into another | `03-ARRAYS/Day-03/code/q09_copy_array.c` | [x] |
| 10 | Replace negatives with 0 | `03-ARRAYS/Day-03/code/q10_replace_negatives.c` | [x] |
| Extra | Sum of two arrays | `03-ARRAYS/1D-Arrays/code/sum_two_arrays.c`, `03-ARRAYS/1D-Arrays/code/sum_two_arrays_duplicate.c` | [x] |
| Extra | Total + average of 5 marks | `03-ARRAYS/1D-Arrays/code/total_average_marks.c` | [x] |

## Day 3 extra - Multidimensional array project

Question source: `C/Assignmenmt/Amit Kumar - multidimentional array-Assignment.pdf`

| Question | Solved as | Status |
| --- | --- | --- |
| Store marks for 5 departments x 3 students x 5 subjects; show each student's total and average for a chosen department | `03-ARRAYS/3D-Arrays/code/three_d_array_marks.c` | [x] |
| Print a 2D array (supporting example) | `03-ARRAYS/2D-Arrays/code/print_2d_array.c` | [x] |
| Print a 3D array (supporting example) | `03-ARRAYS/3D-Arrays/code/print_3d_array.c` | [x] |

## Day 4 - Strings (13 lab questions)

Question source: `C/Assignmenmt/Amit_Kumar_Lab4_Day4_Assignment.docx`
(solved; source programs in `04-STRINGS/Day-04/code/`).

| # | Question | Solved as | Status |
| --- | --- | --- | --- |
| 1 | String length with `strlen()` | `04-STRINGS/Day-04/code/q01_string_length.c` | [x] |
| 2 | Copy string with `strcpy()` | `04-STRINGS/Day-04/code/q02_string_copy.c` | [x] |
| 3 | Compare strings with `strcmp()` | `04-STRINGS/Day-04/code/q03_string_compare.c` | [x] |
| 4 | Join strings with `strcat()` | `04-STRINGS/Day-04/code/q04_string_concatenate.c` | [x] |
| 5 | Longer of two strings | `04-STRINGS/Day-04/code/q05_longer_string.c` | [x] |
| 6 | Password check with `strcmp()` | `04-STRINGS/Day-04/code/q06_password_check.c` | [x] |
| 7 | Append `.txt` with `strcat()` | `04-STRINGS/Day-04/code/q07_add_extension.c` | [x] |
| 8 | Concatenate + total character count | `04-STRINGS/Day-04/code/q08_concat_and_length.c` | [x] |
| 9 | Print vowels in a string | `04-STRINGS/Day-04/code/q09_print_vowels.c` | [x] |
| 10 | Classify each character (lower/upper/digit/special) | `04-STRINGS/Day-04/code/q10_char_classify.c` | [x] |
| 11 | Simple login system | `04-STRINGS/Day-04/code/q11_login_system.c` | [x] |
| 12 | Secure password creator | `04-STRINGS/Day-04/code/q12_password_creator.c` | [x] |
| 13 | Secure authentication (register + login) | `04-STRINGS/Day-04/code/q13_secure_authentication.c` | [x] |

## Extra programs in `C/` (beyond the assignment questions)

| Program | What it does | Status |
| --- | --- | --- |
| `01-BEGINNER/Day-01/code/hello_world.c` | Print "Hello" and "World" | [x] |
| `01-BEGINNER/Day-01/code/unary_operators.c` | Unary `+ -` operators | [x] |
| `01-BEGINNER/Day-02/code/even_odd_check.c` | Even/odd check (if-else) | [x] |
| `01-BEGINNER/Day-02/code/hot_or_cold.c` | Hot if > 30 else cold | [x] |
| `01-BEGINNER/Day-02/code/adult_or_minor.c` | Adult/minor check | [x] |
| `01-BEGINNER/Day-02/code/positive_negative_zero.c` | Positive/negative/zero | [x] |
| `01-BEGINNER/Day-02/code/do_while_demo.c` | do-while vs while | [x] |
| `01-BEGINNER/Day-02/code/stars_row_do_while.c` | N stars with do-while | [x] |
| `02-CORE-C/Operators/code/increment_decrement_operators.c` | Pre/post ++ and -- | [x] |
| `02-CORE-C/Operators/code/increment_expression_eval1.c` | `z = x++ * --y` | [x] |
| `02-CORE-C/Operators/code/increment_expression_eval2.c` | `k = ++i * j--` | [x] |
| `12-ADVANCED-C/code/undefined_increment_behavior.c` | UB mixing ++ in one expression | [x] |
| `12-ADVANCED-C/code/undefined_increment_behavior2.c` | `q = ++p * p++` (UB) | [x] |
| `05-POINTERS/code/pointer_sizeof_demo.c` | Pointer + sizeof (look-ahead) | [x] |
| `08-STRUCTURES-UNIONS/code/student_management.c` | Student management (structs - look-ahead) | [~] |

---

## Course practice files (the drills, by module)

- `01-BEGINNER/Day-01/PRACTICE.md` - Day-1 question set as practice drills
- `01-BEGINNER/Day-02/PRACTICE.md` - Day-2 question set as practice drills
- `03-ARRAYS/PRACTICE.md` - array practice levels 1-6 + Day-3 question set
- `04-STRINGS/PRACTICE.md` - string practice levels 1-6 + Day-4 question set
- `TEMPLATES/Day-XX/PRACTICE.md` - the blank template for future days
