# Course Progress

The single source of truth for what is done. Statuses used:
`Not Started`, `In Progress`, `Completed`, `Needs Revision`.

**Rule:** a topic is `Completed` only after lesson + practice + MCQ + debugging
are actually done. Confidence is a 5-point scale (1 = just saw it, 5 = can
solve new problems unaided).

## Daily log

| Day | Topic | Status | Practice | Assignment | Confidence |
| --- | --- | --- | --- | --- | --- |
| Day 1 | C fundamentals (intro, printf/scanf, variables, data types, operators, basic programs) | Completed | `C/Beginner/*.c` re-run; Day-1 Q1-Q18 in assignment | `Amit_Kumar_CDay1_Assignment.docx` (20 Qs + MCQ bank) | 3 |
| Day 2 | Decision making, switch, loops, patterns | Completed | `C/Day2/q01-q20` | `Amit_Kumar_Lab2_Day2_Assignment.pdf` | 4 |
| Day 3 | Arrays: 1D/2D/3D, search, insert, delete, reverse, copy, compare | Completed | `C/Arrays/*.c`, `C/Day3/*.c` | `Amit_Kumar_Lab3_Day3_Assignment.docx` + multidim array assignment | 3 |
| Day 4 | Strings: strlen/strcpy/strcmp/strcat, input methods, char classification, login/password apps | Completed | `C/Day4/q01-q13` | `Amit_Kumar_Lab4_Day4_Assignment.docx` | 3 |

## Topic status

| Topic | Status | Evidence | Confidence |
| --- | --- | --- | --- |
| Intro to C, program structure, compilation | Completed | Day-1 assignment Explain Q1-Q7 | 3 |
| printf/scanf, format specifiers | Completed | `print_variables.c`, `hello_world.c`, Day-1 Q | 4 |
| Variables, identifiers, constants, literals, keywords | Completed | Day-1 assignment Explain Q16-Q20 | 3 |
| Data types (int/float/double/char), sizeof | Completed | `print_variables.c`, `pointer_sizeof_demo.c` | 3 |
| Arithmetic, unary, increment/decrement operators | Completed | `binary_arithmetic*.c`, `unary_operators.c`, Day-1 Q19-20 | 3 |
| if / if-else / else-if ladder | Completed | `C/Day2/q01-q05`, grade programs | 4 |
| Nested if | Completed | max-of-three, leap year (Day2 q06/q07) | 4 |
| switch | Completed | calculator, vowel (Day2 q08/q09) | 4 |
| Ternary operator | Not Started | - | - |
| for loop | Completed | `C/Day2/q10-q18` | 4 |
| while loop | Completed | `C/Day2/q19-q20` | 4 |
| do-while loop | Completed | `do_while_demo.c`, `stars_row_do_while.c` | 3 |
| Nested loops, patterns | Completed | square/right-triangle patterns | 4 |
| break / continue | Needs Practice | only conceptual questions in Day-2 doc | 2 |
| Arrays: declaration, initialization, indexing | Completed | Day-3 assignment MCQ + programs | 3 |
| Array traversal, input/output | Completed | all Day-3 programs | 4 |
| Sum, average | Completed | `total_average_marks.c`, `sum_two_arrays.c` | 4 |
| Largest element | Completed | `largest_in_array.c`, Day-3 q03 | 4 |
| Smallest element | Not Started | - | - |
| Even/odd counting | Completed | `count_even_odd*.c`, Day-3 q04 | 4 |
| Linear search | Completed | `linear_search_array.c`, Day-3 q02 | 4 |
| Insertion | Completed | `insert_element_array.c`, Day-3 q01 | 3 |
| Deletion | Completed | `delete_element_array.c`, Day-3 q06 | 3 |
| Reverse / print reverse | Completed | `reverse_array.c`, Day-3 q05 | 4 |
| Copy | Completed | `copy_array`, Day-3 q09 | 4 |
| Compare (identical) | Completed | Day-3 q08 | 4 |
| Swap first/last | Completed | Day-3 q07 | 4 |
| Replace negatives with 0 | Completed | Day-3 q10 | 4 |
| 2D arrays | Needs Practice | `print_2d_array.c` + MCQs only | 2 |
| 3D arrays | Needs Practice | `print_3d_array.c`, `three_d_array_marks.c` | 2 |
| Array memory, row-major, address formula | Needs Practice | Day-3 Explain Q2-Q3 only | 2 |
| Array bounds / garbage values / buffer overflow | Needs Practice | Day-3 Explain Q6-Q8 only | 2 |
| Sorting | Not Started | - | - |
| Strings basics, null terminator | Completed | Day-4 q01-q05 | 3 |
| String input (scanf %s, %[^\n], fgets) | Completed | Day-4 q09/q10/q13 | 3 |
| strlen | Completed | Day-4 q01/q05/q08 | 4 |
| strcpy | Completed | Day-4 q02 | 4 |
| strcmp | Completed | Day-4 q03/q06/q11 | 4 |
| strcat | Completed | Day-4 q04/q07/q08 | 4 |
| strchr | Needs Practice | used once in q10/q12 | 2 |
| 2D char arrays (array of strings) | Needs Practice | Day-4 Explain Q4-Q5 only | 2 |
| isupper/islower/isdigit | Completed | Day-4 q10/q12/q13 | 3 |
| String buffer overflow | Needs Practice | Day-4 Explain Q5 only | 2 |
| Functions | Not Started | next lesson | - |
| Pointers | Needs Practice | one demo only (`pointer_sizeof_demo.c`) | 1 |
| Recursion | Not Started | - | - |
| Structures / Unions / Enums | Not Started | (project file exists, not a lesson) | - |
| Dynamic memory | Not Started | - | - |
| File handling | Not Started | - | - |
| Preprocessor | Not Started | - | - |
| Command-line arguments | Not Started | - | - |
| Advanced C / undefined behaviour | Needs Practice | `C/Advanced/undefined_increment_behavior*.c` | 1 |

## Weekly goal (current)

- [ ] Re-run every `C/Arrays/` and `C/Day3/` program from scratch (no peeking)
      to move Arrays 1D confidence to 4-5.
- [ ] Write the missing Day-1 programs (SI, CI, BMI, temp conversions,
      percentage, discount, speed, net salary) in `C-PROGRAMMING-COURSE/02-CORE-C/Input-Output/code/`.
- [ ] Next lesson: Functions (Day 5).

## How to update this file

After any lesson, update the Daily log table and the Topic status table, then
run the "Add today's lesson" checklist in `00-COURSE-README.md`.
