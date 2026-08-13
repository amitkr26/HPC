# 12 - Advanced C

## Status

**Needs Practice** - only the "undefined behaviour" warning topic exists so far.

## What exists

- `12-ADVANCED-C/code/undefined_increment_behavior.c` - expressions mixing pre/post
  increments (some lines are undefined behaviour; output shown for gcc 6.3.0)
- `12-ADVANCED-C/code/undefined_increment_behavior2.c` - `q = ++p * p++` with `p=4`
  (undefined behaviour)

These were studied as a **warning topic**: never rely on expressions that
modify a variable more than once.

## Planned advanced topics

1. Bitwise operators (`& | ^ ~ << >>`)
2. Function pointers
3. Linked lists (singly, doubly)
4. `const`, storage classes, `static`
5. Command-line arguments (`argc`, `argv`) - Level 13 in roadmap

## Prerequisites

Pointers, structures, dynamic memory, and file handling all come first.
