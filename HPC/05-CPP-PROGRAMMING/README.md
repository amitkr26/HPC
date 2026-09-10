# C++ Programming Course

The C++ course. It mirrors the same living, structured layout as the C course:
numbered topic folders, each with `01-CONCEPTS/` (theory -> syntax -> MCQ ->
debugging), `02-EXAMPLES/` (code), `03-PRACTICE/`, and `04-ASSIGNMENTS/`.

> **Status: course in progress** - basics through classes/STL, exam practice.

## Folder layout

```
05-CPP-PROGRAMMING/
├── README.md                  <- you are here
├── 00-COURSE-START/           <- overview, roadmap, progress tracker
├── COURSE-MATERIAL/           <- assignment sheets + lecture PDFs
│   ├── ASSIGNMENTS/
│   └── REFERENCE/
├── 01-CPP-BASICS/             <- program structure, iostream, cout/cin
├── 02-FUNCTIONS/              <- overloading, default args, variadic
├── 03-STL/                    <- vectors, maps, lists
├── 04-OOP/                    <- classes, constructors, inheritance
├── 05-POINTERS-AND-MEMORY/    <- new/delete, deep & shallow copy
├── 06-ADVANCED-CPP/           <- templates, lambdas, smart pointers
├── 07-PRACTICE/               <- extra practice programs
├── 08-ASSIGNMENTS/            <- day-by-day submitted solutions
└── 09-ARCHIVE/                <- in-progress / retired attempts
```

## Compilation

All examples compile with MinGW g++ (GCC 6.3.0):

```bash
C:\MinGW\bin\g++.exe program.cpp -o program.exe
program.exe
```

## Honesty rule (same as C course)

A program existing in a folder does **not** mean it is understood.

- **Studied** - saw it in a lesson/assignment
- **Practiced** - ran and modified it myself
- **Understood** - can explain it and answer viva questions
- **Mastered** - can solve new problems with it without help

## Start here

Open `00-COURSE-START/COURSE-OVERVIEW.md`, then jump into
`01-CPP-BASICS/01-CONCEPTS/`.
