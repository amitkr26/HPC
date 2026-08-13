# String Input

## What it is

Different ways to read a string, and when each is right:

- `scanf("%s", s)` - reads one word, stops at space/newline. No `&` needed.
- `scanf("%[^\n]", s)` - reads a whole line including spaces, up to newline.
- `scanf("%49s", s)` - bounded word read (max 49 chars + null).
- `fgets(s, sizeof(s), stdin)` - reads a line safely; keeps the newline.
- `s[strcspn(s, "\n")] = '\0';` - strip that newline.

## Status

Completed (Day 4). Confidence 3/5 - `fgets` details need practice.

## Code

- `04-STRINGS/Day-04/code/q09_print_vowels.c` - `%[^\n]`
- `04-STRINGS/Day-04/code/q10_char_classify.c` - `%99[^\n]`
- `04-STRINGS/Day-04/code/q13_secure_authentication.c` - `fgets` + `strcspn` + `getchar` flush

## Key rules

- No `&` with `%s`/`%[^\n]` (the array name is already an address).
- `scanf` + `fgets` in the same program need buffer flushing (`getchar()`
  loop) because `scanf` leaves the newline behind.
- Bounded reads (`%49s`, `sizeof`) prevent overflow.

## Common mistakes

- `scanf("%[^\n]", s)` after a previous `scanf` - reads nothing (newline still
  waiting). Flush first.
- `fgets` leaving `\n` in the string (use `strcspn` to remove).
- No width limit on `%s` -> user can overflow the array.
