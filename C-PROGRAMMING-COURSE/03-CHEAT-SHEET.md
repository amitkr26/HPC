# C Cheat Sheet

Revision-oriented reference. Sections marked **(future)** are for reference
only - they have not been covered in the course yet (see `02-PROGRESS.md`).

## printf format specifiers

| Specifier | Type | Example |
| --- | --- | --- |
| `%d` | int | `printf("%d", 42);` |
| `%f` | float | `printf("%.2f", 3.14159);` |
| `%lf` | double | `printf("%lf", 3.14159);` |
| `%c` | char | `printf("%c", 'A');` |
| `%s` | string (char array) | `printf("%s", name);` |
| `%lu` | unsigned long (size_t, strlen result) | `printf("%lu", strlen(s));` |
| `%%` | literal percent | `printf("%%");` |

Widths/precision: `%5d` (width 5), `%.2f` (2 decimals), `%-10s` (left align).

## scanf format specifiers

Same `%d %f %lf %c %s` as above. `scanf` needs addresses: `&var`.

- `scanf("%d", &num);`
- `scanf(" %c", &ch);` - leading space skips leftover newline
- `scanf("%[^\n]", str);` - read until newline (includes spaces)
- `scanf("%49s", str);` - safe bounded word read
- Return value = number of successful conversions (useful for validation).

## Data types (typical sizes on this MinGW setup)

| Type | Size | Range (approx.) | Specifier |
| --- | --- | --- | --- |
| `int` | 4 bytes | -2.1e9 .. 2.1e9 | `%d` |
| `unsigned int` | 4 bytes | 0 .. 4.3e9 | `%u` |
| `char` | 1 byte | -128 .. 127 | `%c` |
| `float` | 4 bytes | ~6-7 digits precision | `%f` |
| `double` | 8 bytes | ~15-16 digits precision | `%lf` |

`sizeof` returns bytes: `sizeof(int)` is typically 4.

## Operators

- Arithmetic: `+ - * / %` (`/` on ints = integer division, `%` = remainder)
- Unary: `++ -- - +`
- Pre-increment `++i`: increment first, then use. Post `i++`: use first, then increment.
- Relational: `> < >= <= == !=`
- Logical: `&& || !`
- Assignment: `= += -= *= /= %=`
- Ternary: `condition ? value_if_true : value_if_false`  **(not yet practised)**
- `&` = address-of, `*` = dereference  **(pointers in progress)**

> Warning: `a++ + ++a` style expressions are **undefined behaviour** - never
> rely on them. See `12-ADVANCED-C/code/undefined_increment_behavior*.c`.

## Conditions

```c
if (condition) { ... }
else if (condition) { ... }
else { ... }

switch (value) {          /* value must be int or char */
    case 1: ...; break;
    case 'a': ...; break;
    default: ...;
}
```

Nested if example (max of three) and leap-year logic live in
`01-BEGINNER/Day-02/code/assignment/q06_max_of_three_nested_if.c / q07_leap_year_nested_if.c`.

## Loops

```c
for (i = 0; i < n; i++) { ... }   /* known count */
while (condition) { ... }         /* check first */
do { ... } while (condition);     /* runs at least once; needs trailing ; */
```

- `break` exits the loop/switch immediately.
- `continue` skips to the next iteration.
- Nested loops: `for(row=1; row<=n; row++) { for(col=1; col<=row; col++) ... }`

## Arrays

```c
int arr[5] = {10, 20, 30, 40, 50};     /* initialization */
int a[5]; for(i=0;i<5;i++) scanf("%d", &a[i]);   /* run-time input */
int mat[3][4];                          /* 2D: rows x cols */
int cube[2][3][4];                      /* 3D */
```

- Indexing starts at **0**; last valid index is `n-1`. Out of range =
  undefined behaviour (garbage/crash).
- Length: `int n = sizeof(arr) / sizeof(arr[0]);` (works only in the scope
  where `arr` is a real array, not after it decays to a pointer).
- 2D stored row-major: address = `base + (i * cols + j) * sizeof(elem)`.
- Partial initialization zero-fills the rest: `int a[5]={1,2,3};` -> `a[4]==0`.
- Uninitialized local arrays hold **garbage**, not 0.

## Strings

```c
char s[20] = "Hello";      /* 'H','e','l','l','o','\0' */
char *p = "Hello";          /* string literal (read-only) */
```

- Every string ends with `'\0'` (null terminator). String functions stop there.
- `strlen(s)` -> length (does not count `'\0'`). Returns `size_t`.
- `strcpy(dest, src)` -> copy src into dest (dest must be big enough).
- `strcmp(a, b)` -> 0 if equal, negative if a<b, positive if a>b.
- `strcat(dest, src)` -> append src to dest (dest needs spare space).
- `strchr(s, ch)` -> pointer to first `ch` or NULL.
- **Never** compare strings with `==` (compares addresses). Use `strcmp`.
- Safe line input: `fgets(s, sizeof(s), stdin);` then
  `s[strcspn(s, "\n")] = '\0';` to strip the newline.
- 2D char array = array of strings: `char names[3][10] = {"Amit","Rohan","Priya"};`
- Buffer overflow: writing more chars than the array holds corrupts memory.

## ctype.h

```c
isupper(c)  islower(c)  isdigit(c)  isalpha(c)  isalnum(c)  isspace(c)
toupper(c)  tolower(c)
```

Return non-zero if true. Use for password/character validation.

## Functions (future)

```c
return_type name(parameters);
return_type name(parameters) { ... return value; }
```

## Pointers (in progress)

```c
int x = 5;   int *p = &x;   printf("%d", *p);   /* 5 */
```

## Structures (future)

```c
struct Student { int roll; char name[50]; float marks; };
```

## Dynamic memory / File handling / Preprocessor (future)

```c
malloc() calloc() realloc() free();
fopen("f.txt","r") fscanf fprintf fgets fclose();
#define MAX 100    #include <stdio.h>    #ifdef
```

## Common compiler errors

| Error | Cause | Fix |
| --- | --- | --- |
| `expected ';'` | missing `;` after a statement | add `;` |
| `'xxx' undeclared` | typo / missing declaration | declare or fix spelling |
| `redefinition of 'main'` | two `main()` in one file | keep one |
| `implicit declaration of function` | missing `#include` / prototype | add header |
| `too few arguments to 'printf'` | format string has more `%` than args | match them |
| `statement with no effect` | `if(x=5)` instead of `if(x==5)` | use `==` |

## Common runtime errors

| Error | Cause | Fix |
| --- | --- | --- |
| Garbage value | uninitialized local variable/array | initialize |
| Out-of-range output | wrong loop bound `<=` vs `<` | use `< n` |
| `scanf` skipping input | leftover `\n` from previous `scanf` | `scanf(" %c", &ch)` or clear buffer |
| Stack/console crash | buffer overflow, out-of-bounds index | respect array bounds |
| Wrong division result | integer division truncates | cast: `total / 5.0` |
