# 16 - Mini Projects

Small projects that use only concepts already learned. Rule: **no project may
require a topic that has not been taught yet** (see `01-ROADMAP.md`).

## Project ladder

| Stage | Concept group | Project | Location |
| --- | --- | --- | --- |
| After fundamentals | I/O, conditions, loops | Calculator | `01-BEGINNER/Day-02/code/assignment/q08_calculator_switch.c`, `02-CORE-C/Conditions/code/calculator_switch*.c` |
| After fundamentals | if-else | ATM machine | `01-BEGINNER/Day-02/code/assignment/atm_simple.c`, `02-CORE-C/Conditions/code/atm_if_else*.c` |
| After fundamentals | loops + conditions | **Number guessing game** | `code/01_number_guessing_game.c` (new) |
| After arrays | arrays, 2D, search, loops | **Student marks manager** | `code/02_student_marks_manager.c` (new) |
| After arrays | arrays | 3D department marks | `03-ARRAYS/3D-Arrays/code/three_d_array_marks.c` |
| After strings | strings, ctype | Password validator / login | `04-STRINGS/Day-04/code/q12_password_creator.c`, `q11_login_system.c`, `q13_secure_authentication.c` |
| After strings | strings | **Word counter / text analyzer** | `code/03_word_counter.c` (new) |
| After functions+arrays+structures | structs, functions, pointers | **Student management system** | `08-STRUCTURES-UNIONS/code/student_management.c` (planned for Level 9) |

## New course projects (`code/`)

| File | Concepts used | Notes |
| --- | --- | --- |
| `01_number_guessing_game.c` | loops, conditions, `rand()` | player vs computer |
| `02_student_marks_manager.c` | 2D arrays, search, totals, menu | no structs/functions yet |
| `03_word_counter.c` | strings, ctype.h, `%[^\n]` | words/chars/vowels/digits |

Each compiles independently with gcc. They are starting points - improve them
as you learn.

## Rules for adding a project

1. Only use learned concepts.
2. One self-contained `.c` file, snake_case name, header comment explaining it.
3. Compile-check with gcc before finishing.
4. Add a row to the ladder above and a `code/` file.
