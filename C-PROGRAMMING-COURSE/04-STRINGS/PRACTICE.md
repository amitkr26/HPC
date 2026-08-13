# String Practice - Levels 1 to 6

Work in order. Update confidence in `02-PROGRESS.md` after each level.

## Level 1 - Basic (understand the syntax)

1. Declare `char name[20] = "Amit";` and print it with `%s`.
2. Print `strlen("Hello")` and explain why it is not 6.
3. Copy `"Copy me"` into a second array with `strcpy` and print both.
4. Compare `"abc"` with `"abc"` and `"abc"` with `"abd"` using `strcmp`;
   print the three possible results.
5. Join `"C "` and `"Programming"` with `strcat` and print the result.

## Level 2 - Logic (reasoning)

1. `char a[20]="Hello", b[]="World";` - after `strcat(a,b)`, what is the size
   of the text in `a`, and how much room is left? (10 chars, 9 slots left +
   null)
2. Why does `if("hello" == "hello")` NOT reliably work?
3. What is printed by `printf("%d %d", strlen("abc"), sizeof("abc"));`?
   (3 and 4 - strlen excludes `'\0'`, sizeof includes it)
4. `char s[5]="Hello";` - compile? (warning/error) What happens at runtime?
5. After `scanf("%s", s)` with input "hello world", what does `s` contain?
   ("hello" - `%s` stops at space)

## Level 3 - Coding (complete C programs)

1. Reverse a string and print it.
2. Count vowels and consonants in a string.
3. Count how many times a specific character appears.
4. Check whether a string is a palindrome.
5. Remove all spaces from a string.
6. Check whether one string occurs inside another (use `strstr`).
7. Convert the whole string to uppercase (use `toupper`).
8. Print only the digits from a string.

## Level 4 - Debugging (find and fix)

1. `char s1[5]="Hello"; char s2[5]; strcpy(s2,s1);` - what overflows?
2. `if(s1 == s2)` - why wrong, how to fix?
3. `scanf("%[^\n]", s);` run twice in a row - second read gets nothing. Why?
4. `printf("%d", strlen(s));` - warning; fix with `%lu`.
5. `strcat(a, b);` where `a` is exactly `"abc"` in `char a[4]` - what happens?
6. `while(s[i] != NULL)` - what is wrong? (`NULL` vs `'\0'`)

## Level 5 - Interview / Viva

1. Why is `'\0'` needed in a string? (Lab-4 Explain Q1)
2. Differentiate `strlen`, `strcpy`, `strcmp`, `strcat` with examples
   (Lab-4 Explain Q2).
3. Difference between `==` and `strcmp` for strings (Lab-4 Explain Q3).
4. What is a 2D character array? Declare and initialize one (Lab-4 Explain Q4).
5. What happens if a string longer than the row is stored?
   (Lab-4 Explain Q5 - buffer overflow, undefined behaviour)
6. When should you use `fgets` over `scanf("%s")`?

## Level 6 - Challenge (multiple concepts)

1. Word counter: read a sentence, count words, characters (no spaces), vowels,
   and digits.
2. Password validator with rules (length, upper, lower, digit, special) and
   specific error messages - you already wrote one as `C/Day4/q12_password_creator.c`;
   rewrite it from memory.
3. Text analyzer: input a name, validate it (only letters), store the name in
   an array of names, print the sorted list later (sorting comes later - for
   now just print all entered names).
4. Phonebook: store N names and phone numbers as a 2D char array with a menu
   (add, display, search by name).
