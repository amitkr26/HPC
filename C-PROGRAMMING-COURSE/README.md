# C Programming Course

A structured, progressive C programming curriculum built from real daily learning. This repository contains a complete learning path from absolute beginner to advanced C topics, with theory, examples, practice programs, assignments, MCQs, debugging guides, and projects.

## What This Repository Contains

- **Structured Course Modules** - 13 main topics organized by prerequisite order
- **180+ C Programs** - Real code written during daily learning sessions
- **Assignments** - Teacher-given lab assignments with solutions
- **MCQs & Quizzes** - Topic-wise multiple choice questions with answers
- **Debugging Guides** - Common errors and how to fix them
- **Mini Projects** - Applied projects using learned concepts
- **Revision Materials** - Cheat sheets, important programs, viva questions
- **Complete Learning History** - Archived original files in `99-ARCHIVE/`

## Who This Course Is For

- Absolute beginners learning C as their first programming language
- Students following a structured C programming curriculum
- Anyone wanting to review C fundamentals through advanced topics
- Self-learners who want a clear learning path with practice material

## Prerequisites

- A C compiler (GCC recommended - MinGW on Windows, GCC on Linux/macOS)
- Basic computer literacy
- No prior programming experience required

## How to Use This Repository

### Recommended Learning Order

Follow the numbered folders in sequence:

```
00-COURSE-START/        → Start here! Course overview, roadmap, setup guide
01-C-BASICS/            → Program structure, variables, I/O, data types
02-OPERATORS/           → Arithmetic, unary, increment/decrement, expressions
03-CONDITIONALS/        → if, else-if, switch, nested conditions
04-LOOPS/               → for, while, do-while, nested loops
05-PATTERNS/            → Star/number pattern problems
06-ARRAYS/              → 1D, 2D, 3D arrays, searching, sorting basics
07-STRINGS/             → String basics, functions (strlen, strcpy, etc.), I/O
08-FUNCTIONS/           → Functions, call by value/reference, storage classes
09-RECURSION/           → Recursive functions, base cases, classic problems
10-POINTERS/            → Pointers, arithmetic, arrays, double pointers
11-STRUCTURES-UNIONS-ENUMS/ → Structures, unions, enums, nested structs
12-DYNAMIC-MEMORY/      → malloc, calloc, realloc, free, dynamic structures
13-FILE-HANDLING/       → File I/O, modes, struct file operations
```

### Each Topic Folder Contains

```
XX-TOPIC/
├── 01-CONCEPTS/        → Theory, syntax, README files
├── 02-EXAMPLES/        → Working code examples
├── 03-PRACTICE/        → Practice programs (graded by difficulty)
├── 04-ASSIGNMENTS/     → Teacher-given lab assignments
└── 05-REVISION/        → Summary materials (where applicable)
```

### Study Approach

1. **Read** the CONCEPTS folder (THEORY.md, SYNTAX.md, README.md)
2. **Study** the EXAMPLES - compile and run each program
3. **Practice** the PRACTICE programs - modify, experiment, break them
4. **Solve** the ASSIGNMENTS - these are graded lab exercises
5. **Test** yourself with MCQs in `17-MCQ-AND-QUIZZES/`
6. **Review** common errors in `16-DEBUGGING/`
7. **Build** mini-projects in `19-MINI-PROJECTS/` after relevant topics

## Course Roadmap

See [`00-COURSE-START/COURSE-ROADMAP.md`](00-COURSE-START/COURSE-ROADMAP.md) for the detailed learning path with prerequisites, resources, and milestones.

## Topic Index

See [`00-COURSE-START/TOPIC-INDEX.md`](00-COURSE-START/TOPIC-INDEX.md) for a searchable map of every concept to its location.

## Practice Strategy

See [`00-COURSE-START/PRACTICE-INDEX.md`](00-COURSE-START/PRACTICE-INDEX.md) for every instructor question mapped to its solved program.

## Assignment Index

See [`18-ASSIGNMENTS/ASSIGNMENTS-README.md`](18-ASSIGNMENTS/ASSIGNMENTS-README.md) for all assignments organized by day/topic.

## Compilation

All `.c` files are designed to compile with standard GCC:

```bash
gcc program.c -o program
./program          # Linux/macOS
program.exe        # Windows
```

For math functions (pow, sqrt), link with `-lm`:

```bash
gcc program.c -o program -lm
```

## Repository Structure

```
C-PROGRAMMING-COURSE/
├── README.md                    # This file
├── 00-COURSE-START/             # Course entry point
│   ├── COURSE-OVERVIEW.md
│   ├── COURSE-ROADMAP.md
│   ├── PROGRESS-TRACKER.md
│   ├── TOPIC-INDEX.md
│   ├── PRACTICE-INDEX.md
│   └── DAY-TEMPLATE-*.md        # Templates for new lessons
├── 01-C-BASICS/ through 13-FILE-HANDLING/  # 13 main topics
├── 14-PREPROCESSOR/             # Not yet covered
├── 15-STORAGE-CLASSES/          # Covered in Functions
├── 16-DEBUGGING/                # Common errors by topic
├── 17-MCQ-AND-QUIZZES/          # MCQs organized by topic
├── 18-ASSIGNMENTS/              # All assignments by day
├── 19-MINI-PROJECTS/            # Applied projects
├── 20-FINAL-PROJECTS/           # Capstone projects (empty - future)
├── 21-REVISION/                 # Cheat sheets, viva questions, etc.
└── 99-ARCHIVE/                  # Original flat history, duplicates, old structure
```

## Progress Tracking

The course uses honest self-assessment:
- **Studied** - Saw it in lesson/assignment
- **Practiced** - Ran and modified it myself
- **Understood** - Can explain it and answer viva questions
- **Mastered** - Can solve new problems with it without help

See [`00-COURSE-START/PROGRESS-TRACKER.md`](00-COURSE-START/PROGRESS-TRACKER.md) for current status.

## Contributing

This is a personal learning repository. The structure follows the actual learning journey. If you find errors in code or documentation, feel free to suggest corrections.

## License

This repository contains personal learning material. Course assignments and teacher materials belong to their respective authors. Code written by the student is free to use for learning purposes.

---

**Start Learning:** Open [`00-COURSE-START/COURSE-OVERVIEW.md`](00-COURSE-START/COURSE-OVERVIEW.md) → [`01-C-BASICS/01-CONCEPTS/`](01-C-BASICS/01-CONCEPTS/)