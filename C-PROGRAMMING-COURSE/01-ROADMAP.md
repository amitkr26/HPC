# C Programming Roadmap

The complete progression from absolute beginner to advanced C, based on what
actually exists in this workspace. Status tags:

- `DONE` - studied through a real lesson/assignment (see `02-PROGRESS.md` for
  confidence levels).
- `[ ]` - planned, not started yet.
- `PARTIAL` - only touched lightly (a single program or MCQ), needs practice.

> **Status of each level is based on real files, not on what "a course should
> cover".** If a topic has only one stray program, it says so.

---

## LEVEL 1 - C Fundamentals  (Day 1)  [DONE]

- What is C? Mid-level language, history context
- Program structure, `main()`, `return 0;`
- `#include <stdio.h>` and why
- `printf()` / `scanf()`, address-of `&`
- Variables, identifiers, naming rules
- Constants, literals, keywords
- Data types: `int`, `float`, `double`, `char`
- Format specifiers: `%d %f %c %s %lf`
- Arithmetic operators `+ - * / %`
- Unary operators, pre/post increment `++ --`
- Type conversion basics, integer vs float division
- Simple programs: sum, swap, area, perimeter, SI, CI, BMI,
  temperature conversion, percentage, discount, speed, net salary

**Material:** `01-BEGINNER/Day-01/` -> `C/Assignmenmt/Amit_Kumar_CDay1_Assignment.docx`,
`01-BEGINNER/`

> Note: several Day-1 problems (simple interest, compound interest, BMI,
> Celsius/Fahrenheit, percentage, discount, speed, net salary) exist only in
> the assignment document, not as separate `.c` files. Good re-practice targets.

## LEVEL 2 - Decision Making  (Day 2)  [DONE]

- `if`, `if-else`
- `else-if` ladder (grades)
- Nested `if` (max of three, leap year)
- `switch` (calculator, vowel/consonant)
- `break` in switch
- Ternary operator  `[ ]` not yet practised
- Relational and logical operators

**Material:** `01-BEGINNER/Day-02/` -> `01-BEGINNER/Day-02/code/`, `01-BEGINNER/` (decision files),
`02-CORE-C/` (nested-if variants)

## LEVEL 3 - Loops  (Day 2)  [DONE]

- `for` loop
- `while` loop
- `do-while` loop (difference from `while`)
- Nested loops (square, right-triangle patterns)
- `break`, `continue` (conceptual questions done; practice with them in loops)
- Loop patterns: counting, series, sum, tables, alphabets, stars

**Material:** `01-BEGINNER/Day-02/` -> `01-BEGINNER/Day-02/code/assignment/q10-q20`, `01-BEGINNER/` (loops)

## LEVEL 4 - Arrays  (Day 3)  [DONE]

- What is an array? declaration, initialization, indexing
- Compile-time vs run-time initialization
- Traversal, input, output
- Sum, average (marks)
- Largest element, smallest  `[ ]` (only largest done)
- Even/odd counting
- Linear search
- Insertion, deletion, reverse, copy, compare, swap first/last
- Replace elements (negatives -> 0)
- 2D arrays, 3D arrays, memory layout (row-major), address formula
- Array length via `sizeof(arr)/sizeof(arr[0])`
- Bounds errors, garbage values, buffer overflow
- Sorting  `[ ]` NOT STARTED

**Material:** `03-ARRAYS/` -> `03-ARRAYS/`, `03-ARRAYS/Day-03/code/`,
`C/Assignmenmt/Amit_Kumar_Lab3_Day3_Assignment.docx`

## LEVEL 5 - Strings  (Day 4)  [DONE]

- Character arrays vs strings
- Null terminator `'\0'`
- String input: `scanf("%s")`, `%[^\n]`, `fgets()` + `strcspn`
- `strlen()`, `strcpy()`, `strcmp()`, `strcat()`, `strchr()`
- String comparison: `==` vs `strcmp()`
- 2D character arrays (array of strings)
- Buffer overflow with strings
- Character classification: `isupper()`, `islower()`, `isdigit()` (`ctype.h`)
- Mini applications: login, password validation, authentication

**Material:** `04-STRINGS/` -> `04-STRINGS/Day-04/code/`,
`C/Assignmenmt/Amit_Kumar_Lab4_Day4_Assignment.docx`

## LEVEL 6 - Functions  [DONE]

- Why functions, declaration vs definition, prototype
- Parameters, return values
- Call by value, call by reference (pointers)
- `void` functions
- Scope, local/global variables
- Storage classes (auto, static, extern, register)
- Recursive functions (factorial, fibonacci, GCD, power)
- Function with arrays
- Returning multiple values via pointers

**Material:** `06-FUNCTIONS/Day-06/` -> `06-FUNCTIONS/Day-06/code/`,
`C/Day5/`, `C/Assignmenmt/Amit_Kumar_Lab5_Day5_Assignment.docx`

## LEVEL 7 - Pointers  [DONE]

- What is a pointer, address-of `&`, dereference `*`
- `sizeof` (demo program: `pointer_sizeof_demo.c`)
- Pointer arithmetic, arrays and pointers, pointer/array relationship
- Pointers as function arguments, call by reference
- Pointers and strings
- Array of pointers, pointer to pointer (double pointer)
- Swapping using pointers
- Reverse array using pointers

**Material:** `05-POINTERS/Day-05/` -> `05-POINTERS/Day-05/code/`,
`C/Day7/`, `C/Day8/`, `C/Assignmenmt/Amit_Kumar_Lab7_Day7_Assignment.docx`

## LEVEL 8 - Recursion  [DONE]

- Base case + recursive case
- Factorial, Fibonacci, sum of digits, power, GCD
- Recursion vs iteration, call stack, stack overflow
- Tower of Hanoi
- String reversal using recursion
- Palindrome check using recursion
- Linear search using recursion
- Bubble sort using recursion
- Decimal to binary using recursion

**Material:** `07-RECURSION/Day-07/` -> `07-RECURSION/Day-07/code/`

## LEVEL 9 - Structures, Unions, Enums  [DONE]

- `struct`, members, arrays of structs
- Nested structs, struct pointers (`->`)
- `typedef` with structures
- `union`, memory sharing
- `enum`
- Structure as function arguments (by value and pointer)
- Sorting structures
- Student management system

**Material:** `08-STRUCTURES-UNIONS/Day-08/` -> `08-STRUCTURES-UNIONS/Day-08/code/`,
`C/Day6/`, `C/Day8/`, `C/Assignmenmt/Amit_Kumar_Lab6_Day6_Assignment.docx`

## LEVEL 10 - Dynamic Memory  [DONE]

- `malloc()`, `calloc()`, `realloc()`, `free()`
- Heap vs stack
- Memory leaks, dangling pointers
- Dynamic arrays, dynamic 2D arrays
- Dynamic structures
- Dynamic strings

**Material:** `09-DYNAMIC-MEMORY/Day-09/` -> `09-DYNAMIC-MEMORY/Day-09/code/`

## LEVEL 11 - File Handling  [DONE]

- `fopen()` modes (r, w, a, r+, w+, a+)
- `fprintf/fscanf`, `fgets/fputs`
- `fgetc/fputc` (character I/O)
- `fclose()`, error handling (NULL check)
- File positioning (fseek, ftell, rewind)
- End of file detection (feof)
- Struct file I/O
- Simple encryption/decryption

**Material:** `10-FILE-HANDLING/Day-10/` -> `10-FILE-HANDLING/Day-10/code/`

## LEVEL 12 - Preprocessor  [ ] NOT STARTED

- `#define` constants and macros
- `#include`, header guards
- Conditional compilation `#ifdef` etc.

## LEVEL 13 - Command-Line Arguments  [ ] NOT STARTED

- `int main(int argc, char *argv[])`
- `atoi()`, etc.

## LEVEL 14 - Advanced C  [PARTIAL - undefined behaviour only]

- Evaluation order and undefined behaviour
  (`12-ADVANCED-C/code/undefined_increment_behavior*.c` - studied as a warning topic)
- Function pointers, bitwise operators, linked lists
  [all not started]

## Projects (throughout)

See `16-MINI-PROJECTS/`. Projects must only use already-learned concepts.

- After fundamentals: calculator (exists), ATM (exists), number guessing
- After arrays: student marks manager, inventory, employee records
- After strings: password validator (exists), word counter, text analyzer
- After functions+arrays+structures: **student management system**
  (exists at `08-STRUCTURES-UNIONS/code/student_management.c`)

---

## Where I am now

All levels 1-11 complete with theory, syntax, examples, practice, MCQ, and
debugging materials.

Next lesson: **Level 12 - Preprocessor**.

## Gap checklist (what exists on paper but not as separate code)

- Day 1: simple interest, compound interest, BMI, temp conversions,
  percentage, discount, speed, net salary (in assignment docx only).
- Smallest element in array, sorting, ternary operator (never practised).
- The `==` vs `strcmp` and bounds topics exist as explanations only.
