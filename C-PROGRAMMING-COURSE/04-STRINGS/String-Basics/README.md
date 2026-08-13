# String Basics

## What it is

A string is a `char` array whose text is ended by a null terminator `'\0'`.
`"Hello"` is stored as `'H','e','l','l','o','\0'`. All string functions scan
up to `'\0'`.

## Status

Completed (Day 4). Confidence 3/5.

## Code

- `C/Day4/q01_string_length.c` - read a string, print `strlen()`
- `C/Day4/q05_longer_string.c` - compare two lengths, print the longer

## Key rules

- The array must reserve space for the null: `char s[6] = "Hello";` (5 chars + 1).
- `strlen` does NOT count `'\0'` (result for "Hello" is 5).
- `printf("%s", s)` stops printing exactly before `'\0'`.
- Without `'\0'`, functions read past the end (garbage/crash).

## Common mistakes

- `char s[5] = "Hello";` - no room for `'\0'`, buffer overflow.
- Expecting `strlen("Hi")` to be 3 (it is 2; the null is not counted).
