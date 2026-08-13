# Topic Index

Search any C topic here. Format:

- **Level** = roadmap level
- **Day** = day learned
- **Theory / Code / Practice / Assignment** = where each lives
- **Related** = topics that connect to it

Paths are relative to the workspace root. `C/` files are original learning
history; files inside `C-PROGRAMMING-COURSE/` are course material.

---

## C Fundamentals

### Intro to C, program structure, compilation
- Level: 1 | Day: 1
- Theory: `C/Assignmenmt/Amit_Kumar_CDay1_Assignment.docx` (Explain Q1-Q7)
- Code: `C/Beginner/hello_world.c`
- Related: main(), printf, scanf, preprocessor

### main(), return 0, #include
- Level: 1 | Day: 1
- Theory: Day-1 Explain Q11-Q12
- Code: every `.c` file in `C/`
- Related: compilation process

### printf() / scanf() / format specifiers
- Level: 1 | Day: 1
- Code: `C/Beginner/print_variables.c`, `C/Beginner/sum_of_two_numbers.c`
- Cheat sheet: `03-CHEAT-SHEET.md`
- Related: data types, address-of operator

### Variables, identifiers, naming rules
- Level: 1 | Day: 1
- Theory: Day-1 Explain Q16
- Related: data types, constants

### Constants, literals, keywords
- Level: 1 | Day: 1
- Theory: Day-1 Explain Q17-Q20
- Related: variables

### Data types (int, float, double, char), sizeof
- Level: 1 | Day: 1
- Code: `C/Beginner/print_variables.c`, `C/Intermediate/pointer_sizeof_demo.c`
- Related: format specifiers, operators

### Arithmetic / unary / increment-decrement operators
- Level: 1 | Day: 1
- Code: `C/Beginner/binary_arithmetic.c`, `C/Beginner/binary_arithmetic_input.c`,
  `C/Beginner/unary_operators.c`, `C/Intermediate/increment_decrement_operators.c`,
  `C/Intermediate/increment_expression_eval1.c`, `C/Intermediate/increment_expression_eval2.c`
- Assignment: Day-1 Q19-Q20
- Related: undefined behaviour (`C/Advanced/`)

### Swap two numbers
- Level: 1 | Day: 1
- Code: `C/Beginner/swap_two_numbers.c`
- Assignment: Day-1 Q7
- Related: variables, temp variable pattern

### Basic programs (area, perimeter, SI, CI, BMI, conversions)
- Level: 1 | Day: 1
- Code: `C/Beginner/area_of_square.c`, `C/Beginner/area_of_circle.c`,
  `C/Beginner/circumference_of_circle.c`
- Assignment (theory only, code not yet written): Day-1 Q9-Q18
- Related: arithmetic operators, float division

## Decision Making

### if / if-else
- Level: 2 | Day: 2
- Code: `C/Day2/q01_positive_or_negative.c`, `C/Day2/q02_even_or_odd.c`,
  `C/Day2/q03_adult_or_minor.c`, `C/Day2/q04_hot_or_cold.c`,
  `C/Day2/q05_divisible_by_5.c`, `C/Beginner/even_odd_check.c`, `C/Beginner/positive_negative_zero.c`
- Related: relational/logical operators

### else-if ladder (grades)
- Level: 2 | Day: 2
- Code: `C/Day2/grade_else_if.c`, `C/Intermediate/grade_else_if_ladder.c`,
  `C/Intermediate/grade_else_if_ladder_variant.c`
- Practice: `C-PROGRAMMING-COURSE/02-CORE-C/Conditions/`

### Nested if (max of three, leap year)
- Level: 2 | Day: 2
- Code: `C/Day2/q06_max_of_three_nested_if.c`, `C/Day2/q07_leap_year_nested_if.c`,
  `C/Intermediate/leap_year.c`, `C/Intermediate/salary_increment_nested_if.c`
- Related: conditions, logical operators

### switch (calculator, vowel)
- Level: 2 | Day: 2
- Code: `C/Day2/q08_calculator_switch.c`, `C/Day2/q09_vowel_or_consonant.c`,
  `C/Intermediate/calculator_switch_basic.c`, `C/Intermediate/calculator_switch_safe.c`,
  `C/Intermediate/vowel_or_consonant.c`
- Related: break, if-else

### Ternary operator
- Level: 2 | **Not Started**
- Related: if-else

## Loops

### for loop
- Level: 3 | Day: 2
- Code: `C/Day2/q10_print_1_to_10.c` to `q18_right_triangle_star.c`
- Related: while, do-while, nested loops

### while loop
- Level: 3 | Day: 2
- Code: `C/Day2/q19_stars_row_while.c`, `C/Day2/q20_stars_row_while.c`
- Related: for loop, do-while

### do-while loop
- Level: 3 | Day: 2
- Code: `C/Beginner/do_while_demo.c`, `C/Beginner/stars_row_do_while.c`
- Related: while loop

### Nested loops / patterns
- Level: 3 | Day: 2
- Code: `C/Day2/q16_five_stars_row.c`, `q17_square_star_pattern.c`,
  `q18_right_triangle_star.c`
- Related: for loop, counting

### break / continue
- Level: 3 | Day: 2 (Needs Practice)
- Theory: Day-2 Question Bank (conceptual)
- Related: loops, switch

### Series / summation programs
- Level: 3 | Day: 2
- Code: `C/Beginner/even_series.c`, `C/Beginner/sum_of_odd_numbers.c`,
  `C/Beginner/multiplication_table.c`, `C/Day2/q12_even_1_to_50.c`,
  `C/Day2/q13_divisible_by_3_and_5.c`, `C/Day2/q14_sum_odd_up_to_n.c`,
  `C/Day2/q15_alphabets_a_to_z.c`
- Related: loops, modulo

## Arrays

### Array basics (declaration, initialization, indexing)
- Level: 4 | Day: 3
- Theory: `C/Assignmenmt/Amit_Kumar_Lab3_Day3_Assignment.docx` (MCQ 1-4, Explain 1-2)
- Code: `C/Arrays/`, `C/Day3/`
- Practice: `C-PROGRAMMING-COURSE/03-ARRAYS/1D-Arrays/`
- Related: loops, memory

### Traversal, input, output
- Level: 4 | Day: 3
- Code: `C/Arrays/print_2d_array.c`, `C/Arrays/print_3d_array.c`,
  `C/Arrays/print_reverse_array.c`
- Related: for loops, indexing

### Sum / average
- Level: 4 | Day: 3
- Code: `C/Arrays/total_average_marks.c`, `C/Arrays/sum_two_arrays.c`
- Related: arithmetic, loops

### Largest element
- Level: 4 | Day: 3
- Code: `C/Arrays/largest_in_array.c`, `C/Day3/q03_largest_element.c`
- Related: traversal, comparison
- Smallest: **Not Started**

### Even/odd counting
- Level: 4 | Day: 3
- Code: `C/Arrays/count_even_odd_array.c`, `C/Arrays/count_even_odd_ten_elements.c`,
  `C/Day3/q04_count_even_odd.c`
- Related: modulo, counting

### Linear search
- Level: 4 | Day: 3
- Code: `C/Arrays/linear_search_array.c`, `C/Day3/q02_linear_search.c`
- Practice: `C-PROGRAMMING-COURSE/03-ARRAYS/Searching/`
- Related: loops, break, boolean flag

### Insertion
- Level: 4 | Day: 3
- Code: `C/Arrays/insert_element_array.c`, `C/Day3/q01_insert_element.c`
- Practice: `C-PROGRAMMING-COURSE/03-ARRAYS/Insertion/`
- Related: shifting, indexing

### Deletion
- Level: 4 | Day: 3
- Code: `C/Arrays/delete_element_array.c`, `C/Day3/q06_delete_value.c`
- Practice: `C-PROGRAMMING-COURSE/03-ARRAYS/Deletion/`
- Related: shifting, linear search

### Reverse / print reverse
- Level: 4 | Day: 3
- Code: `C/Arrays/reverse_array.c`, `C/Arrays/print_reverse_array.c`,
  `C/Day3/q05_reverse_array.c`
- Related: indexing, descending loops

### Copy, Compare, Swap first/last, Replace negatives
- Level: 4 | Day: 3
- Code: `C/Day3/q09_copy_array.c`, `C/Day3/q08_arrays_identical.c`,
  `C/Day3/q07_swap_first_last.c`, `C/Day3/q10_replace_negatives.c`
- Related: loops, comparison, assignment

### 2D arrays
- Level: 4 | Day: 3 (Needs Practice)
- Code: `C/Arrays/print_2d_array.c`
- Theory: Day-3 Explain Q3-Q4, MCQ 3/8
- Related: row-major memory, nested loops

### 3D arrays
- Level: 4 | Day: 3 (Needs Practice)
- Code: `C/Arrays/print_3d_array.c`, `C/Arrays/three_d_array_marks.c`
- Assignment: `C/Assignmenmt/Amit Kumar - multidimentional array-Assignment.pdf`
- Theory: Day-3 MCQ 10, Explain Q5(c)
- Related: 2D arrays, nested loops

### Array memory, length formula, bounds, garbage
- Level: 4 | Day: 3 (Needs Practice)
- Theory: Day-3 Explain Q2, Q6-Q8, MCQ 1/4/9
- Related: pointers (future), sizeof

### Sorting
- Level: 4 | **Not Started**
- Related: insertion, searching

## Strings

### String basics, char arrays, null terminator
- Level: 5 | Day: 4
- Theory: `Amit_Kumar_Lab4_Day4_Assignment.docx` (Explain Q1, Q5)
- Code: `C/Day4/q01_string_length.c`
- Related: arrays, pointers (future)

### String input (scanf %s, %[^\n], fgets, strcspn)
- Level: 5 | Day: 4
- Code: `C/Day4/q09_print_vowels.c`, `q10_char_classify.c`, `q13_secure_authentication.c`
- Cheat sheet: `03-CHEAT-SHEET.md`
- Related: stdin buffer, newline handling

### strlen
- Level: 5 | Day: 4
- Code: `C/Day4/q01_string_length.c`, `q05_longer_string.c`, `q08_concat_and_length.c`
- Related: null terminator

### strcpy
- Level: 5 | Day: 4
- Code: `C/Day4/q02_string_copy.c`
- Related: buffer size

### strcmp
- Level: 5 | Day: 4
- Code: `C/Day4/q03_string_compare.c`, `q06_password_check.c`, `q11_login_system.c`
- Theory: Day-4 Explain Q3 (`==` vs strcmp)
- Related: ASCII comparison

### strcat
- Level: 5 | Day: 4
- Code: `C/Day4/q04_string_concatenate.c`, `q07_add_extension.c`, `q08_concat_and_length.c`
- Related: buffer overflow

### strchr
- Level: 5 | Day: 4 (Needs Practice)
- Code: `C/Day4/q10_char_classify.c`, `q12_password_creator.c`
- Related: character search

### ctype.h functions
- Level: 5 | Day: 4
- Code: `C/Day4/q10_char_classify.c`, `q12_password_creator.c`, `q13_secure_authentication.c`
- Related: character classification

### 2D character arrays (array of strings)
- Level: 5 | Day: 4 (Needs Practice)
- Theory: Day-4 Explain Q4-Q5
- Related: 2D arrays

### String applications (login, password, auth)
- Level: 5 | Day: 4
- Code: `C/Day4/q11_login_system.c`, `q12_password_creator.c`, `q13_secure_authentication.c`
- Related: loops, strcmp, ctype.h

## Pointers

### Pointer basics, address-of, dereference, sizeof
- Level: 7 | Day: (partial)
- Code: `C/Intermediate/pointer_sizeof_demo.c`
- Status: **Needs Practice** (only one demo program)
- Related: arrays, strings, functions (future)

## Advanced C

### Undefined behaviour / evaluation order
- Level: 14 | Day: (partial)
- Code: `C/Advanced/undefined_increment_behavior.c`,
  `C/Advanced/undefined_increment_behavior2.c`,
  `C/Intermediate/increment_expression_eval1.c`, `increment_expression_eval2.c`
- Status: **Needs Practice** (warning topic)

## Projects

### ATM machine
- Level: 2/3 | Day: 2
- Code: `C/Day2/atm_simple.c`, `C/Intermediate/atm_if_else.c`, `C/Intermediate/atm_if_else_variant.c`
- Related: if-else, nested if, money/balance

### Student marks (3D array project)
- Level: 4 | Day: 3
- Code: `C/Arrays/three_d_array_marks.c`
- Assignment: `Amit Kumar - multidimentional array-Assignment.pdf`
- Related: 3D arrays

### Student management system (structures)
- Level: 9 | Day: project file only
- Code: `C/Project/student_management.c`
- Status: **written ahead of course** - revisit after Structures (Level 9)
- Related: structs, functions, pointers, strings, arrays
