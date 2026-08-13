# Topic Index

Search any C topic here. Format:

- **Level** = roadmap level
- **Day** = day learned
- **Theory / Code / Practice / Assignment** = where each lives
- **Related** = topics that connect to it

Paths are relative to the workspace root. `C/` files are original learning
history; files inside `C-PROGRAMMING-COURSE/` are course material.

For every instructor-given practice question and its solved program, see
`PRACTICE-INDEX.md`.

---

## C Fundamentals

### Intro to C, program structure, compilation
- Level: 1 | Day: 1
- Theory: `C/Assignmenmt/Amit_Kumar_CDay1_Assignment.docx` (Explain Q1-Q7)
- Code: `01-BEGINNER/Day-01/code/hello_world.c`
- Related: main(), printf, scanf, preprocessor

### main(), return 0, #include
- Level: 1 | Day: 1
- Theory: Day-1 Explain Q11-Q12
- Code: every `.c` file in `C/`
- Related: compilation process

### printf() / scanf() / format specifiers
- Level: 1 | Day: 1
- Code: `01-BEGINNER/Day-01/code/print_variables.c`, `01-BEGINNER/Day-01/code/sum_of_two_numbers.c`
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
- Code: `01-BEGINNER/Day-01/code/print_variables.c`, `05-POINTERS/code/pointer_sizeof_demo.c`
- Related: format specifiers, operators

### Arithmetic / unary / increment-decrement operators
- Level: 1 | Day: 1
- Code: `01-BEGINNER/Day-01/code/binary_arithmetic.c`, `01-BEGINNER/Day-01/code/binary_arithmetic_input.c`,
  `01-BEGINNER/Day-01/code/unary_operators.c`, `02-CORE-C/Operators/code/increment_decrement_operators.c`,
  `02-CORE-C/Operators/code/increment_expression_eval1.c`, `02-CORE-C/Operators/code/increment_expression_eval2.c`
- Assignment: Day-1 Q19-Q20
- Related: undefined behaviour (`12-ADVANCED-C/code/`)

### Swap two numbers
- Level: 1 | Day: 1
- Code: `01-BEGINNER/Day-01/code/swap_two_numbers.c`
- Assignment: Day-1 Q7
- Related: variables, temp variable pattern

### Basic programs (area, perimeter, SI, CI, BMI, conversions)
- Level: 1 | Day: 1
- Code: `01-BEGINNER/Day-01/code/area_of_square.c`, `01-BEGINNER/Day-01/code/area_of_circle.c`,
  `01-BEGINNER/Day-01/code/circumference_of_circle.c`
- Assignment (theory only, code not yet written): Day-1 Q9-Q18
- Related: arithmetic operators, float division

## Decision Making

### if / if-else
- Level: 2 | Day: 2
- Code: `01-BEGINNER/Day-02/code/assignment/q01_positive_or_negative.c`, `01-BEGINNER/Day-02/code/assignment/q02_even_or_odd.c`,
  `01-BEGINNER/Day-02/code/assignment/q03_adult_or_minor.c`, `01-BEGINNER/Day-02/code/assignment/q04_hot_or_cold.c`,
  `01-BEGINNER/Day-02/code/assignment/q05_divisible_by_5.c`, `01-BEGINNER/Day-02/code/even_odd_check.c`, `01-BEGINNER/Day-02/code/positive_negative_zero.c`
- Related: relational/logical operators

### else-if ladder (grades)
- Level: 2 | Day: 2
- Code: `01-BEGINNER/Day-02/code/assignment/grade_else_if.c`, `02-CORE-C/Conditions/code/grade_else_if_ladder.c`,
  `02-CORE-C/Conditions/code/grade_else_if_ladder_variant.c`
- Practice: `C-PROGRAMMING-COURSE/02-CORE-C/Conditions/`

### Nested if (max of three, leap year)
- Level: 2 | Day: 2
- Code: `01-BEGINNER/Day-02/code/assignment/q06_max_of_three_nested_if.c`, `01-BEGINNER/Day-02/code/assignment/q07_leap_year_nested_if.c`,
  `02-CORE-C/Conditions/code/leap_year.c`, `02-CORE-C/Conditions/code/salary_increment_nested_if.c`
- Related: conditions, logical operators

### switch (calculator, vowel)
- Level: 2 | Day: 2
- Code: `01-BEGINNER/Day-02/code/assignment/q08_calculator_switch.c`, `01-BEGINNER/Day-02/code/assignment/q09_vowel_or_consonant.c`,
  `02-CORE-C/Conditions/code/calculator_switch_basic.c`, `02-CORE-C/Conditions/code/calculator_switch_safe.c`,
  `02-CORE-C/Conditions/code/vowel_or_consonant.c`
- Related: break, if-else

### Ternary operator
- Level: 2 | **Not Started**
- Related: if-else

## Loops

### for loop
- Level: 3 | Day: 2
- Code: `01-BEGINNER/Day-02/code/assignment/q10_print_1_to_10.c` to `q18_right_triangle_star.c`
- Related: while, do-while, nested loops

### while loop
- Level: 3 | Day: 2
- Code: `01-BEGINNER/Day-02/code/assignment/q19_stars_row_while.c`, `01-BEGINNER/Day-02/code/assignment/q20_stars_row_while.c`
- Related: for loop, do-while

### do-while loop
- Level: 3 | Day: 2
- Code: `01-BEGINNER/Day-02/code/do_while_demo.c`, `01-BEGINNER/Day-02/code/stars_row_do_while.c`
- Related: while loop

### Nested loops / patterns
- Level: 3 | Day: 2
- Code: `01-BEGINNER/Day-02/code/assignment/q16_five_stars_row.c`, `q17_square_star_pattern.c`,
  `q18_right_triangle_star.c`
- Related: for loop, counting

### break / continue
- Level: 3 | Day: 2 (Needs Practice)
- Theory: Day-2 Question Bank (conceptual)
- Related: loops, switch

### Series / summation programs
- Level: 3 | Day: 2
- Code: `01-BEGINNER/Day-02/code/even_series.c`, `01-BEGINNER/Day-02/code/sum_of_odd_numbers.c`,
  `01-BEGINNER/Day-02/code/multiplication_table.c`, `01-BEGINNER/Day-02/code/assignment/q12_even_1_to_50.c`,
  `01-BEGINNER/Day-02/code/assignment/q13_divisible_by_3_and_5.c`, `01-BEGINNER/Day-02/code/assignment/q14_sum_odd_up_to_n.c`,
  `01-BEGINNER/Day-02/code/assignment/q15_alphabets_a_to_z.c`
- Related: loops, modulo

## Arrays

### Array basics (declaration, initialization, indexing)
- Level: 4 | Day: 3
- Theory: `C/Assignmenmt/Amit_Kumar_Lab3_Day3_Assignment.docx` (MCQ 1-4, Explain 1-2)
- Code: `03-ARRAYS/`, `03-ARRAYS/Day-03/code/`
- Practice: `C-PROGRAMMING-COURSE/03-ARRAYS/1D-Arrays/`
- Related: loops, memory

### Traversal, input, output
- Level: 4 | Day: 3
- Code: `03-ARRAYS/2D-Arrays/code/print_2d_array.c`, `03-ARRAYS/3D-Arrays/code/print_3d_array.c`,
  `03-ARRAYS/1D-Arrays/code/print_reverse_array.c`
- Related: for loops, indexing

### Sum / average
- Level: 4 | Day: 3
- Code: `03-ARRAYS/1D-Arrays/code/total_average_marks.c`, `03-ARRAYS/1D-Arrays/code/sum_two_arrays.c`
- Related: arithmetic, loops

### Largest element
- Level: 4 | Day: 3
- Code: `03-ARRAYS/1D-Arrays/code/largest_in_array.c`, `03-ARRAYS/Day-03/code/q03_largest_element.c`
- Related: traversal, comparison
- Smallest: **Not Started**

### Even/odd counting
- Level: 4 | Day: 3
- Code: `03-ARRAYS/1D-Arrays/code/count_even_odd_array.c`, `03-ARRAYS/1D-Arrays/code/count_even_odd_ten_elements.c`,
  `03-ARRAYS/Day-03/code/q04_count_even_odd.c`
- Related: modulo, counting

### Linear search
- Level: 4 | Day: 3
- Code: `03-ARRAYS/Searching/code/linear_search_array.c`, `03-ARRAYS/Day-03/code/q02_linear_search.c`
- Practice: `C-PROGRAMMING-COURSE/03-ARRAYS/Searching/`
- Related: loops, break, boolean flag

### Insertion
- Level: 4 | Day: 3
- Code: `03-ARRAYS/Insertion/code/insert_element_array.c`, `03-ARRAYS/Day-03/code/q01_insert_element.c`
- Practice: `C-PROGRAMMING-COURSE/03-ARRAYS/Insertion/`
- Related: shifting, indexing

### Deletion
- Level: 4 | Day: 3
- Code: `03-ARRAYS/Deletion/code/delete_element_array.c`, `03-ARRAYS/Day-03/code/q06_delete_value.c`
- Practice: `C-PROGRAMMING-COURSE/03-ARRAYS/Deletion/`
- Related: shifting, linear search

### Reverse / print reverse
- Level: 4 | Day: 3
- Code: `03-ARRAYS/1D-Arrays/code/reverse_array.c`, `03-ARRAYS/1D-Arrays/code/print_reverse_array.c`,
  `03-ARRAYS/Day-03/code/q05_reverse_array.c`
- Related: indexing, descending loops

### Copy, Compare, Swap first/last, Replace negatives
- Level: 4 | Day: 3
- Code: `03-ARRAYS/Day-03/code/q09_copy_array.c`, `03-ARRAYS/Day-03/code/q08_arrays_identical.c`,
  `03-ARRAYS/Day-03/code/q07_swap_first_last.c`, `03-ARRAYS/Day-03/code/q10_replace_negatives.c`
- Related: loops, comparison, assignment

### 2D arrays
- Level: 4 | Day: 3 (Needs Practice)
- Code: `03-ARRAYS/2D-Arrays/code/print_2d_array.c`
- Theory: Day-3 Explain Q3-Q4, MCQ 3/8
- Related: row-major memory, nested loops

### 3D arrays
- Level: 4 | Day: 3 (Needs Practice)
- Code: `03-ARRAYS/3D-Arrays/code/print_3d_array.c`, `03-ARRAYS/3D-Arrays/code/three_d_array_marks.c`
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
- Code: `04-STRINGS/Day-04/code/q01_string_length.c`
- Related: arrays, pointers (future)

### String input (scanf %s, %[^\n], fgets, strcspn)
- Level: 5 | Day: 4
- Code: `04-STRINGS/Day-04/code/q09_print_vowels.c`, `q10_char_classify.c`, `q13_secure_authentication.c`
- Cheat sheet: `03-CHEAT-SHEET.md`
- Related: stdin buffer, newline handling

### strlen
- Level: 5 | Day: 4
- Code: `04-STRINGS/Day-04/code/q01_string_length.c`, `q05_longer_string.c`, `q08_concat_and_length.c`
- Related: null terminator

### strcpy
- Level: 5 | Day: 4
- Code: `04-STRINGS/Day-04/code/q02_string_copy.c`
- Related: buffer size

### strcmp
- Level: 5 | Day: 4
- Code: `04-STRINGS/Day-04/code/q03_string_compare.c`, `q06_password_check.c`, `q11_login_system.c`
- Theory: Day-4 Explain Q3 (`==` vs strcmp)
- Related: ASCII comparison

### strcat
- Level: 5 | Day: 4
- Code: `04-STRINGS/Day-04/code/q04_string_concatenate.c`, `q07_add_extension.c`, `q08_concat_and_length.c`
- Related: buffer overflow

### strchr
- Level: 5 | Day: 4 (Needs Practice)
- Code: `04-STRINGS/Day-04/code/q10_char_classify.c`, `q12_password_creator.c`
- Related: character search

### ctype.h functions
- Level: 5 | Day: 4
- Code: `04-STRINGS/Day-04/code/q10_char_classify.c`, `q12_password_creator.c`, `q13_secure_authentication.c`
- Related: character classification

### 2D character arrays (array of strings)
- Level: 5 | Day: 4 (Needs Practice)
- Theory: Day-4 Explain Q4-Q5
- Related: 2D arrays

### String applications (login, password, auth)
- Level: 5 | Day: 4
- Code: `04-STRINGS/Day-04/code/q11_login_system.c`, `q12_password_creator.c`, `q13_secure_authentication.c`
- Related: loops, strcmp, ctype.h

## Pointers

### Pointer basics, address-of, dereference, sizeof
- Level: 7 | Day: (partial)
- Code: `05-POINTERS/code/pointer_sizeof_demo.c`
- Status: **Needs Practice** (only one demo program)
- Related: arrays, strings, functions (future)

## Advanced C

### Undefined behaviour / evaluation order
- Level: 14 | Day: (partial)
- Code: `12-ADVANCED-C/code/undefined_increment_behavior.c`,
  `12-ADVANCED-C/code/undefined_increment_behavior2.c`,
  `02-CORE-C/Operators/code/increment_expression_eval1.c`, `increment_expression_eval2.c`
- Status: **Needs Practice** (warning topic)

## Projects

### ATM machine
- Level: 2/3 | Day: 2
- Code: `01-BEGINNER/Day-02/code/assignment/atm_simple.c`, `02-CORE-C/Conditions/code/atm_if_else.c`, `02-CORE-C/Conditions/code/atm_if_else_variant.c`
- Related: if-else, nested if, money/balance

### Student marks (3D array project)
- Level: 4 | Day: 3
- Code: `03-ARRAYS/3D-Arrays/code/three_d_array_marks.c`
- Assignment: `Amit Kumar - multidimentional array-Assignment.pdf`
- Related: 3D arrays

### Student management system (structures)
- Level: 9 | Day: project file only
- Code: `08-STRUCTURES-UNIONS/code/student_management.c`
- Status: **written ahead of course** - revisit after Structures (Level 9)
- Related: structs, functions, pointers, strings, arrays
