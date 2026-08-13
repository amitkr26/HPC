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
| 1 | Declare two int variables, assign, display | `C/Beginner/print_variables.c` | [x] |
| 2 | Input name, print "Welcome NAME to C Programming" | (not written) | [ ] |
| 3 | First name, last name, age with proper names | (not written) | [ ] |
| 4 | Area of square (input side) | `C/Beginner/area_of_square.c` | [x] |
| 5 | Constant pi, circumference of circle | `C/Beginner/circumference_of_circle.c` | [x] |
| 6 | Area of circle (input radius) | `C/Beginner/area_of_circle.c` | [x] |
| 7 | Swap two numbers | `C/Beginner/swap_two_numbers.c` | [x] |
| 8 | Two ints: + - * / (float) % | `C/Beginner/binary_arithmetic_input.c` | [x] |
| 9 | Simple Interest | (not written) | [ ] |
| 10 | Add, subtract, multiply, divide two numbers | `C/Beginner/binary_arithmetic.c`, `C/Intermediate/calculator_switch_basic.c` | [~] |
| 11 | Compound Interest | (not written) | [ ] |
| 12 | BMI | (not written) | [ ] |
| 13 | Celsius to Fahrenheit | (not written) | [ ] |
| 14 | Fahrenheit to Celsius | (not written) | [ ] |
| 15 | Percentage of marks (5 subjects) | `C/Arrays/total_average_marks.c` | [~] |
| 16 | Discounted price | (not written) | [ ] |
| 17 | Speed = distance / time | (not written) | [ ] |
| 18 | Net salary = basic + allowance - deductions | `C/Intermediate/salary_increment_float.c`, `C/Intermediate/salary_increment_nested_if.c` | [~] |
| 19 | Predict output: `x++` / `++x` sequence | `C/Intermediate/increment_decrement_operators.c` | [x] |
| 20 | Predict output: `k = ++i * j--` | `C/Intermediate/increment_expression_eval2.c`, `C/Advanced/undefined_increment_behavior.c` | [x] |

Missing programs (Q2, Q3, Q9, Q11-Q14, Q16, Q17): practice targets - write them.

## Day 2 - Conditions, Loops, Patterns (20 lab questions + bonus)

Question source: `C/Assignmenmt/Amit_Kumar_Lab2_Day2_Assignment.pdf`
(solved, with markdown copy at `C/Day2/Amit_Lab2.md`).

| # | Question (short) | Solved as | Status |
| --- | --- | --- | --- |
| 1 | Positive or negative | `C/Day2/q01_positive_or_negative.c` | [x] |
| 2 | Even or odd | `C/Day2/q02_even_or_odd.c` | [x] |
| 3 | Adult or minor (18) | `C/Day2/q03_adult_or_minor.c` | [x] |
| 4 | Hot or cold (>= 30) | `C/Day2/q04_hot_or_cold.c` | [x] |
| 5 | Divisible by 5 | `C/Day2/q05_divisible_by_5.c` | [x] |
| 6 | Maximum of three (nested if) | `C/Day2/q06_max_of_three_nested_if.c`, `C/Intermediate/max_of_three_nested_if_duplicate.c` | [x] |
| 7 | Leap year (nested if) | `C/Day2/q07_leap_year_nested_if.c`, `C/Intermediate/leap_year.c` | [x] |
| 8 | Calculator with switch | `C/Day2/q08_calculator_switch.c`, `C/Intermediate/calculator_switch_safe.c` | [x] |
| 9 | Vowel or consonant (switch) | `C/Day2/q09_vowel_or_consonant.c`, `C/Intermediate/vowel_or_consonant.c` | [x] |
| 10 | Print 1 to 10 | `C/Day2/q10_print_1_to_10.c`, `C/Beginner/print_1_to_10_duplicate.c` | [x] |
| 11 | Multiplication table (1-10) | `C/Day2/q11_multiplication_table.c`, `C/Beginner/multiplication_table.c` | [x] |
| 12 | Even numbers 1 to 50 | `C/Day2/q12_even_1_to_50.c`, `C/Beginner/even_series.c` | [x] |
| 13 | Numbers 1-100 divisible by 3 and 5 | `C/Day2/q13_divisible_by_3_and_5.c`, `C/Beginner/multiple_of_3_and_5.c` | [x] |
| 14 | Sum of odd numbers up to N | `C/Day2/q14_sum_odd_up_to_n.c`, `C/Beginner/sum_of_odd_numbers.c` | [x] |
| 15 | Alphabets a to z | `C/Day2/q15_alphabets_a_to_z.c`, `C/Beginner/alphabets_a_to_z_duplicate.c` | [x] |
| 16 | Five stars in a row | `C/Day2/q16_five_stars_row.c`, `C/Beginner/five_stars_row_duplicate.c` | [x] |
| 17 | Square star pattern (N rows) | `C/Day2/q17_square_star_pattern.c`, `C/Beginner/square_star_pattern_duplicate.c` | [x] |
| 18 | Right triangle star pattern | `C/Day2/q18_right_triangle_star.c`, `C/Beginner/right_triangle_star_pattern_duplicate.c` | [x] |
| 19 | Stars in a row (while) | `C/Day2/q19_stars_row_while.c` | [x] |
| 20 | Stars in a row (while) | `C/Day2/q20_stars_row_while.c` (duplicate of Q19) | [~] |
| Bonus | Grade with else-if ladder | `C/Day2/grade_else_if.c`, `C/Intermediate/grade_else_if_ladder.c`, `C/Intermediate/grade_else_if_ladder_variant.c` | [x] |
| Bonus | ATM (if-else only) | `C/Day2/atm_simple.c`, `C/Intermediate/atm_if_else.c`, `C/Intermediate/atm_if_else_variant.c` | [x] |

## Day 3 - Arrays (10 lab questions)

Question source: `C/Assignmenmt/Amit_Kumar_Lab3_Day3_Assignment.docx`
(solved; source programs in `C/Day3/`).

| # | Question | Solved as | Status |
| --- | --- | --- | --- |
| 1 | Insert an element at a position | `C/Day3/q01_insert_element.c`, `C/Arrays/insert_element_array.c` | [x] |
| 2 | Linear search | `C/Day3/q02_linear_search.c`, `C/Arrays/linear_search_array.c` | [x] |
| 3 | Largest element | `C/Day3/q03_largest_element.c`, `C/Arrays/largest_in_array.c` | [x] |
| 4 | Count even and odd | `C/Day3/q04_count_even_odd.c`, `C/Arrays/count_even_odd_array.c`, `C/Arrays/count_even_odd_ten_elements.c` | [x] |
| 5 | Reverse an array | `C/Day3/q05_reverse_array.c`, `C/Arrays/reverse_array.c`, `C/Arrays/print_reverse_array.c` | [x] |
| 6 | Delete a value | `C/Day3/q06_delete_value.c`, `C/Arrays/delete_element_array.c` | [x] |
| 7 | Swap first and last | `C/Day3/q07_swap_first_last.c` | [x] |
| 8 | Two arrays identical | `C/Day3/q08_arrays_identical.c` | [x] |
| 9 | Copy one array into another | `C/Day3/q09_copy_array.c` | [x] |
| 10 | Replace negatives with 0 | `C/Day3/q10_replace_negatives.c` | [x] |
| Extra | Sum of two arrays | `C/Arrays/sum_two_arrays.c`, `C/Arrays/sum_two_arrays_duplicate.c` | [x] |
| Extra | Total + average of 5 marks | `C/Arrays/total_average_marks.c` | [x] |

## Day 3 extra - Multidimensional array project

Question source: `C/Assignmenmt/Amit Kumar - multidimentional array-Assignment.pdf`

| Question | Solved as | Status |
| --- | --- | --- |
| Store marks for 5 departments x 3 students x 5 subjects; show each student's total and average for a chosen department | `C/Arrays/three_d_array_marks.c` | [x] |
| Print a 2D array (supporting example) | `C/Arrays/print_2d_array.c` | [x] |
| Print a 3D array (supporting example) | `C/Arrays/print_3d_array.c` | [x] |

## Day 4 - Strings (13 lab questions)

Question source: `C/Assignmenmt/Amit_Kumar_Lab4_Day4_Assignment.docx`
(solved; source programs in `C/Day4/`).

| # | Question | Solved as | Status |
| --- | --- | --- | --- |
| 1 | String length with `strlen()` | `C/Day4/q01_string_length.c` | [x] |
| 2 | Copy string with `strcpy()` | `C/Day4/q02_string_copy.c` | [x] |
| 3 | Compare strings with `strcmp()` | `C/Day4/q03_string_compare.c` | [x] |
| 4 | Join strings with `strcat()` | `C/Day4/q04_string_concatenate.c` | [x] |
| 5 | Longer of two strings | `C/Day4/q05_longer_string.c` | [x] |
| 6 | Password check with `strcmp()` | `C/Day4/q06_password_check.c` | [x] |
| 7 | Append `.txt` with `strcat()` | `C/Day4/q07_add_extension.c` | [x] |
| 8 | Concatenate + total character count | `C/Day4/q08_concat_and_length.c` | [x] |
| 9 | Print vowels in a string | `C/Day4/q09_print_vowels.c` | [x] |
| 10 | Classify each character (lower/upper/digit/special) | `C/Day4/q10_char_classify.c` | [x] |
| 11 | Simple login system | `C/Day4/q11_login_system.c` | [x] |
| 12 | Secure password creator | `C/Day4/q12_password_creator.c` | [x] |
| 13 | Secure authentication (register + login) | `C/Day4/q13_secure_authentication.c` | [x] |

## Extra programs in `C/` (beyond the assignment questions)

| Program | What it does | Status |
| --- | --- | --- |
| `C/Beginner/hello_world.c` | Print "Hello" and "World" | [x] |
| `C/Beginner/unary_operators.c` | Unary `+ -` operators | [x] |
| `C/Beginner/even_odd_check.c` | Even/odd check (if-else) | [x] |
| `C/Beginner/hot_or_cold.c` | Hot if > 30 else cold | [x] |
| `C/Beginner/adult_or_minor.c` | Adult/minor check | [x] |
| `C/Beginner/positive_negative_zero.c` | Positive/negative/zero | [x] |
| `C/Beginner/do_while_demo.c` | do-while vs while | [x] |
| `C/Beginner/stars_row_do_while.c` | N stars with do-while | [x] |
| `C/Intermediate/increment_decrement_operators.c` | Pre/post ++ and -- | [x] |
| `C/Intermediate/increment_expression_eval1.c` | `z = x++ * --y` | [x] |
| `C/Intermediate/increment_expression_eval2.c` | `k = ++i * j--` | [x] |
| `C/Advanced/undefined_increment_behavior.c` | UB mixing ++ in one expression | [x] |
| `C/Advanced/undefined_increment_behavior2.c` | `q = ++p * p++` (UB) | [x] |
| `C/Intermediate/pointer_sizeof_demo.c` | Pointer + sizeof (look-ahead) | [x] |
| `C/Project/student_management.c` | Student management (structs - look-ahead) | [~] |

---

## Course practice files (the drills, by module)

- `01-BEGINNER/Day-01/PRACTICE.md` - Day-1 question set as practice drills
- `01-BEGINNER/Day-02/PRACTICE.md` - Day-2 question set as practice drills
- `03-ARRAYS/PRACTICE.md` - array practice levels 1-6 + Day-3 question set
- `04-STRINGS/PRACTICE.md` - string practice levels 1-6 + Day-4 question set
- `TEMPLATES/Day-XX/PRACTICE.md` - the blank template for future days
