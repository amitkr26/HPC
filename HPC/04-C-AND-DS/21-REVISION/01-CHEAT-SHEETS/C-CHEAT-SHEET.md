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

## Functions

```c
return_type name(parameters);              // prototype
return_type name(parameters) { ... }       // definition
name(arguments);                          // call
```

- Call by value: `func(x)` - copies value, original unchanged
- Call by reference: `func(&x)` - passes address, can modify original
- `void` functions return nothing
- Static variables retain value between calls: `static int count = 0;`
- Recursive functions must have a base case to stop

```c
int add(int a, int b) { return a + b; }
void swap(int *a, int *b) { int t=*a; *a=*b; *b=t; }
int factorial(int n) { return (n<=1) ? 1 : n*factorial(n-1); }
```

## Pointers

```c
int x = 5;
int *p = &x;        // p stores address of x
printf("%d", *p);   // dereference: prints 5
*p = 10;            // change x through pointer
```

- `&` = address-of operator
- `*` = dereference operator
- Pointer arithmetic: `p+1` advances by `sizeof(type)` bytes
- Arrays decay to pointers: `arr == &arr[0]`
- Pass by reference: `func(&x)` in call, `func(int *p)` in definition
- Double pointer: `int **pp = &p;` (pointer to pointer)
- Always initialize pointers; check for NULL before dereferencing

```c
void swap(int *a, int *b) { int t=*a; *a=*b; *b=t; }
int *ptr = arr;  // points to first element
printf("%d", *(ptr+i));  // same as arr[i]
```

## Structures

```c
struct Student {
    int roll;
    char name[50];
    float marks;
};

struct Student s1 = {1, "Amit", 85.5};
s1.roll = 2;                    // dot operator
struct Student *p = &s1;
p->name;                        // arrow operator (pointer)
```

- Arrays of structs: `struct Student class[3];`
- Nested structs: `struct Date { int d,m,y; }; struct Emp { struct Date join; };`
- `typedef struct { ... } Alias;` - no `struct` keyword needed
- `union` - all members share memory (size = largest member)
- `enum Color { RED, GREEN, BLUE };` - named integer constants
- Struct assignment copies all members: `s2 = s1;`

## Dynamic Memory

```c
#include <stdlib.h>
int *p = (int*)malloc(n * sizeof(int));     // uninitialized
int *p = (int*)calloc(n, sizeof(int));      // zero-initialized
p = (int*)realloc(p, new_size * sizeof(int)); // resize
free(p);                                     // release memory
p = NULL;                                    // prevent dangling
```

- Heap (malloc) vs Stack (local variables)
- Always check for NULL after malloc/calloc/realloc
- Always free before losing the pointer
- Memory leak = forgetting to free
- Dynamic 2D array: `int **mat = malloc(rows * sizeof(int*));`

## File Handling

```c
FILE *fp = fopen("file.txt", "r");  // open
// "r" read, "w" write (truncate), "a" append
// "r+" read+write, "w+" read+write (truncate), "a+" read+append

fputc('A', fp);                     // write char
char ch = fgetc(fp);                // read char (EOF at end)
fputs("Hello\n", fp);               // write string
fgets(buf, size, fp);               // read line
fprintf(fp, "%s %d\n", str, num);   // write formatted
fscanf(fp, "%s %d", str, &num);     // read formatted

fseek(fp, 0, SEEK_SET);             // go to beginning
fseek(fp, 0, SEEK_END);             // go to end
long pos = ftell(fp);               // current position
rewind(fp);                         // go to beginning

fclose(fp);                         // always close!
```

- Always check `fopen` return for NULL
- Use `"rb"/"wb"` for binary files
- `feof(fp)` returns non-zero at end of file

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
