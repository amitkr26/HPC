# Course Roadmap

Complete learning progression from beginner to advanced C, based on actual repository content.

## Phase 1: C Fundamentals (Week 1)

### Day 1: Program Structure & Basics
- **Concepts**: What is C, program structure, `main()`, `#include`, compilation process
- **I/O**: `printf()`, `scanf()`, format specifiers (`%d`, `%f`, `%c`, `%s`, `%lf`)
- **Variables**: Declaration, initialization, naming rules, constants
- **Data Types**: `int`, `float`, `double`, `char`, `sizeof`
- **Operators**: Arithmetic (`+`, `-`, `*`, `/`, `%`), integer vs float division
- **Location**: `01-C-BASICS/01-CONCEPTS/`, `01-C-BASICS/02-EXAMPLES/`
- **Practice**: `01-C-BASICS/03-PRACTICE/DAY-01-PRACTICE.md`
- **Assignment**: `18-ASSIGNMENTS/DAY-01/DAY-01-ASSIGNMENT.docx` (20 questions)

### Day 2: Decision Making & Loops
- **Conditionals**: `if`, `if-else`, `else-if` ladder, nested `if`, `switch`
- **Loops**: `for`, `while`, `do-while`, differences, when to use each
- **Control**: `break`, `continue` in loops and switch
- **Patterns**: Nested loops for star/number patterns
- **Location**: `03-CONDITIONALS/`, `04-LOOPS/`, `05-PATTERNS/`
- **Practice**: `03-CONDITIONALS/03-PRACTICE/DAY-02-PRACTICE.md`
- **Assignment**: `18-ASSIGNMENTS/DAY-02/DAY-02-ASSIGNMENT.pdf` (20 questions + bonus)

---

## Phase 2: Core Programming (Week 2)

### Day 3: Arrays
- **1D Arrays**: Declaration, initialization, traversal, input/output
- **Operations**: Sum, average, max/min, even/odd counting
- **Algorithms**: Linear search, insertion, deletion, reverse, copy, compare
- **2D Arrays**: Declaration, traversal, matrix operations
- **3D Arrays**: Multi-dimensional arrays, practical example (student marks)
- **Location**: `06-ARRAYS/01-1D-ARRAYS/`, `06-ARRAYS/02-2D-ARRAYS/`, `06-ARRAYS/03-3D-ARRAYS/`
- **Practice**: `06-ARRAYS/04-PRACTICE/ARRAYS-PRACTICE.md` (6 levels)
- **Assignment**: `18-ASSIGNMENTS/DAY-03/` (10 lab questions + multidimensional project)

### Day 4: Strings
- **Basics**: Char arrays vs strings, null terminator `\0`
- **Input**: `scanf("%s")`, `scanf("%[^\n]")`, `fgets()` + `strcspn()`
- **Functions**: `strlen()`, `strcpy()`, `strcmp()`, `strcat()`, `strchr()`
- **Important**: Never compare strings with `==` (use `strcmp()`)
- **Applications**: Login system, password validation, secure authentication
- **Character Classification**: `isupper()`, `islower()`, `isdigit()` from `ctype.h`
- **Location**: `07-STRINGS/01-CONCEPTS/`, `07-STRINGS/02-EXAMPLES/`, `07-STRINGS/03-PRACTICE/`
- **Practice**: `07-STRINGS/03-PRACTICE/STRINGS-PRACTICE.md` (6 levels)
- **Assignment**: `18-ASSIGNMENTS/DAY-04/` (13 lab questions)

---

## Phase 3: Functions & Advanced Concepts (Week 3-4)

### Day 5: Functions
- **Basics**: Declaration (prototype), definition, call, parameters, return values
- **Call by Value** vs **Call by Reference** (using pointers)
- **Storage Classes**: `auto`, `static`, `extern`, `register`
- **Recursion**: Base case, recursive case, call stack
- **Function with Arrays**: Passing arrays to functions
- **Returning Multiple Values**: Via pointers
- **Location**: `08-FUNCTIONS/01-CONCEPTS/`, `08-FUNCTIONS/02-EXAMPLES/`, `08-FUNCTIONS/03-PRACTICE/`
- **Practice**: `08-FUNCTIONS/03-PRACTICE/FUNCTIONS-PRACTICE.md` (15 problems, 3 levels)
- **Assignment**: `18-ASSIGNMENTS/DAY-05/` (menu calculator, guess game, combined Day 5&6)

### Day 5 (cont): Pointers
- **Basics**: Address-of `&`, dereference `*`, pointer declaration
- **Pointer Arithmetic**: `p+1` advances by `sizeof(type)`
- **Pointers & Arrays**: Array decay, `arr == &arr[0]`, `*(arr+i) == arr[i]`
- **Pointers as Function Arguments**: Call by reference, swapping
- **Double Pointers**: `int **pp = &p;`
- **String Pointers**: `char *str = "Hello";`
- **Location**: `10-POINTERS/01-CONCEPTS/`, `10-POINTERS/02-EXAMPLES/`, `10-POINTERS/03-PRACTICE/`
- **Practice**: `10-POINTERS/03-PRACTICE/POINTERS-PRACTICE.md` (19 problems)
- **Assignment**: `18-ASSIGNMENTS/DAY-07/POINTERS-ASSIGNMENT.pdf` + combined Day 5&6

### Day 6: Recursion
- **Concept**: Function calling itself, base case + recursive case
- **Classic Problems**: Factorial, Fibonacci, GCD, power, sum of digits
- **String Recursion**: Reverse string, palindrome check
- **Array Recursion**: Linear search, bubble sort, array sum
- **Advanced**: Tower of Hanoi, decimal to binary
- **Location**: `09-RECURSION/01-CONCEPTS/`, `09-RECURSION/02-EXAMPLES/`, `09-RECURSION/03-PRACTICE/`
- **Practice**: `09-RECURSION/03-PRACTICE/RECURSION-PRACTICE.md`
- **Assignment**: Part of combined Day 5&6 assignment

### Day 6: Structures, Unions, Enums
- **Structures**: Declaration, members, arrays of structs, nested structs
- **Structure Pointers**: Arrow operator `->`, passing to functions
- **Typedef**: Cleaner syntax with structures
- **Unions**: Shared memory, size = largest member
- **Enums**: Named integer constants
- **Sorting Structures**: Bubble sort on struct arrays
- **Project**: Student management system
- **Location**: `11-STRUCTURES-UNIONS-ENUMS/01-CONCEPTS/`, `11-STRUCTURES-UNIONS-ENUMS/02-EXAMPLES/`, `11-STRUCTURES-UNIONS-ENUMS/03-PRACTICE/`
- **Practice**: `11-STRUCTURES-UNIONS-ENUMS/03-PRACTICE/STRUCTURES-PRACTICE.md`
- **Assignment**: `18-ASSIGNMENTS/DAY-06/DAY-06-ASSIGNMENT.pdf` (student management)

---

## Phase 4: Systems Programming (Week 5)

### Day 7: Dynamic Memory
- **Allocation**: `malloc()`, `calloc()`, `realloc()`
- **Deallocation**: `free()`, preventing memory leaks, dangling pointers
- **Heap vs Stack**: Memory layout
- **Dynamic Arrays**: Runtime-sized arrays
- **Dynamic 2D Arrays**: Pointer-to-pointer approach
- **Dynamic Structures**: `malloc` for structs
- **Dynamic Strings**: `malloc` for strings
- **Location**: `12-DYNAMIC-MEMORY/01-CONCEPTS/`, `12-DYNAMIC-MEMORY/02-EXAMPLES/`, `12-DYNAMIC-MEMORY/03-PRACTICE/`
- **Practice**: `12-DYNAMIC-MEMORY/03-PRACTICE/DYNAMIC-MEMORY-PRACTICE.md`
- **Assignment**: Part of combined assignments

### Day 8: File Handling
- **File Modes**: `r`, `w`, `a`, `r+`, `w+`, `a+` (text and binary)
- **Operations**: `fopen()`, `fclose()`, error checking (NULL)
- **Character I/O**: `fgetc()`, `fputc()`
- **String I/O**: `fgets()`, `fputs()`
- **Formatted I/O**: `fprintf()`, `fscanf()`
- **Positioning**: `fseek()`, `ftell()`, `rewind()`
- **Struct File I/O**: Writing/reading structures
- **Applications**: File copy, encrypt/decrypt, word counter
- **Location**: `13-FILE-HANDLING/01-CONCEPTS/`, `13-FILE-HANDLING/02-EXAMPLES/`, `13-FILE-HANDLING/03-PRACTICE/`
- **Practice**: `13-FILE-HANDLING/03-PRACTICE/FILE-HANDLING-PRACTICE.md`
- **Assignment**: Future - not yet covered

### Day 9: Preprocessor (NOT YET COVERED)
- **Macros**: `#define` constants and function-like macros
- **Headers**: `#include`, header guards
- **Conditional Compilation**: `#ifdef`, `#ifndef`, `#endif`, `#if`, `#else`
- **Location**: `14-PREPROCESSOR/01-CONCEPTS/`
- **Status**: Planned, not started

### Day 10: Advanced Topics (PARTIAL)
- **Undefined Behavior**: Evaluation order, `i++ + ++i` problems
- **Function Pointers**: Not yet covered
- **Bitwise Operators**: Not yet covered
- **Linked Lists**: Not yet covered
- **Command-Line Arguments**: Not yet covered
- **Location**: `16-DEBUGGING/02-EXAMPLES/` (undefined behavior examples)
- **Status**: Only undefined behavior studied as warning topic

---

## Projects (Applied Throughout)

### Mini Projects (After Relevant Topics)
| Project | Concepts Used | Location | After Topic |
|---------|--------------|----------|-------------|
| Number Guessing Game | Loops, conditions, random | `19-MINI-PROJECTS/01-NUMBER-GUESSING/` | Loops |
| Student Marks Manager | Arrays, structs, functions | `19-MINI-PROJECTS/02-STUDENT-MARKS/` | Structs |
| Word Counter | File I/O, strings, pointers | `19-MINI-PROJECTS/03-WORD-COUNTER/` | File Handling |

### Final Projects (Capstone)
- **Location**: `20-FINAL-PROJECTS/`
- **Status**: Not yet started - requires all topics complete

---

## Learning Resources by Topic

| Topic | Theory | Syntax | Examples | Practice | MCQ | Debugging |
|-------|--------|--------|----------|----------|-----|-----------|
| C Basics | ✅ | ✅ | ✅ | ✅ | 01-BASICS | - |
| Operators | ✅ | ✅ | ✅ | ✅ | 01-BASICS | - |
| Conditionals | ✅ | ✅ | ✅ | ✅ | 01-BASICS | - |
| Loops | ✅ | ✅ | ✅ | ✅ | 01-BASICS | - |
| Patterns | - | - | ✅ | ✅ | 01-BASICS | - |
| Arrays (1D/2D/3D) | ✅ | ✅ | ✅ | ✅ | 02-ARRAYS | - |
| Strings | ✅ | ✅ | ✅ | ✅ | 03-STRINGS | - |
| Functions | ✅ | ✅ | ✅ | ✅ | 04-FUNCTIONS | ✅ |
| Pointers | ✅ | ✅ | ✅ | ✅ | 05-POINTERS | ✅ |
| Recursion | ✅ | ✅ | ✅ | ✅ | 08-MIXED | ✅ |
| Structures | ✅ | ✅ | ✅ | ✅ | 06-STRUCTURES | ✅ |
| Dynamic Memory | ✅ | ✅ | ✅ | ✅ | 07-MEMORY | ✅ |
| File Handling | ✅ | ✅ | ✅ | ✅ | 08-MIXED | ✅ |

---

## Current Status

**Completed (with theory, syntax, examples, practice, MCQ, debugging):**
- ✅ Levels 1-11: Fundamentals → File Handling

**Next Lesson:**
- **Level 12: Preprocessor** (`14-PREPROCESSOR/`)

**Partial:**
- Advanced C / Undefined Behavior (warning topic only)

**Not Started:**
- Command-Line Arguments
- Function Pointers
- Bitwise Operators
- Linked Lists
- Full Final Projects

---

## Honesty Rule

> A program existing in a folder does **not** mean it is understood.

- **Studied** - Saw it in lesson/assignment
- **Practiced** - Ran and modified it myself
- **Understood** - Can explain it and answer viva questions
- **Mastered** - Can solve new problems with it without help

When evidence is missing, mark as **Needs Practice**.