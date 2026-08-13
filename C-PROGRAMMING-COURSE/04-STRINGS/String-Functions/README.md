# String Functions

## What it is

The `<string.h>` workhorses: `strlen`, `strcpy`, `strcmp`, `strcat`, `strchr`.

## Status

Completed (Day 4). Confidence: strlen/strcpy/strcmp/strcat 4/5, strchr 2/5.

## Code

| Function | What it does | Program |
| --- | --- | --- |
| `strlen(s)` | returns length (no `'\0'`), type `size_t` | `04-STRINGS/Day-04/code/q01_string_length.c`, `q05_longer_string.c`, `q08_concat_and_length.c` |
| `strcpy(dest, src)` | copies src (incl. `'\0'`) into dest | `04-STRINGS/Day-04/code/q02_string_copy.c` |
| `strcmp(a, b)` | 0 if equal, <0 if a first, >0 if b first | `04-STRINGS/Day-04/code/q03_string_compare.c`, `q06_password_check.c`, `q11_login_system.c` |
| `strcat(dest, src)` | appends src at dest's `'\0'` | `04-STRINGS/Day-04/code/q04_string_concatenate.c`, `q07_add_extension.c`, `q08_concat_and_length.c` |
| `strchr(s, ch)` | pointer to first ch or NULL | `04-STRINGS/Day-04/code/q10_char_classify.c`, `q12_password_creator.c` |

## Key rules

- `strcmp` compares **content**, not addresses. `==` on char arrays compares
  addresses - almost never equal for two separate arrays.
- `strcpy`/`strcat` do NOT check sizes - destination must be big enough.
- `strcat` needs spare room in dest for src plus one null.
- `strlen` returns `size_t` (`%lu`), not `int`.

## Common mistakes

- `if(s1 == s2)` instead of `if(strcmp(s1,s2)==0)`.
- `strcat` into a dest with no spare space (overflow).
- `strcpy` dest smaller than src.
- Printing `strlen` with `%d` (use `%lu` or cast to `(int)`).
