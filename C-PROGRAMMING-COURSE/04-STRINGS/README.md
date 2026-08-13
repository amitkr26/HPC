# 04 - Strings

The strings module (Day 4). Maps every string topic to a program in
`04-STRINGS/Day-04/code/q01-q13` and the solved assignment
(`C/Assignmenmt/Amit_Kumar_Lab4_Day4_Assignment.docx`).

## Progression checklist

1. `[x]` What a string is (char array + `'\0'`)
2. `[x]` String input: `scanf("%s")`, `scanf("%[^\n]")`, `fgets()` + `strcspn`
3. `[x]` String termination and why `'\0'` matters
4. `[x]` `strlen()` - length (no null counted)
5. `[x]` `strcpy()` - copy
6. `[x]` `strcmp()` - compare (returns 0 / negative / positive)
7. `[x]` `strcat()` - join (destination needs spare space)
8. `[x]` `strchr()` - find a character (used, needs more practice)
9. `[x]` String comparison: `==` vs `strcmp()` (theory done)
10. `[x]` Character classification with `ctype.h` (`isupper/islower/isdigit`)
11. `[~]` 2D character arrays (array of strings) - theory only
12. `[x]` String buffer overflow - theory done (Explain Q5)
13. `[x]` Mini applications: login, password creator, authentication

## Module layout

| Sub-module | What it holds |
| --- | --- |
| `String-Basics/` | char arrays, null terminator, strlen |
| `String-Input/` | scanf %s, %[^\n], fgets, strcspn, buffer pitfalls |
| `String-Functions/` | strcpy, strcmp, strcat, strchr |
| `String-Practice/` | practice levels and drills |
| `Day-04/` | the daily record of the strings lesson |

## Source material (preserved in `C/`)

- `04-STRINGS/Day-04/code/q01-q13` - all string programs (`.exe`, input files
  and screenshots remain in the `C/` history)
- `C/Assignmenmt/Amit_Kumar_Lab4_Day4_Assignment.docx` - solved document
  (13 programs + 10 MCQs + 5 Explain answers)

## Honest status

Core functions: solid (confidence 3-4). 2D char arrays, `strchr`, buffer
overflow, `fgets` details: seen but **needs practice**.

See `PRACTICE.md` (levels 1-6 + the Day-4 question set) and `REVISION.md`.
The master question-to-program map is in `PRACTICE-INDEX.md`.
