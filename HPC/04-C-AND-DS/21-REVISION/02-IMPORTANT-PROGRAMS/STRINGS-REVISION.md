# Strings Revision

Revision pack for strings: 10 quick + 10 output + 10 find-the-error + 10
coding + 10 MCQ + 5 viva + 1 mini project. Most items come from the Day-4
assignment (`C/Assignmenmt/Amit_Kumar_Lab4_Day4_Assignment.docx`).

## 10 quick questions

1. What marks the end of a string? (`'\0'`)
2. What does `strlen` return for `"ABC"`? (3)
3. What does `sizeof("ABC")` return? (4)
4. Which function copies one string into another? (`strcpy`)
5. What does `strcmp` return for equal strings? (0)
6. Which function appends one string to another? (`strcat`)
7. What does `strchr(s, 'a')` return if 'a' is missing? (NULL)
8. Can `==` compare two strings by content? (No - it compares addresses)
9. Which input function reads a whole line safely? (`fgets`)
10. What does `strcspn(s, "\n")` give you? (index of the newline, if any)

## 10 output questions

1. `char s[]="Computer"; printf("%d", strlen(s));` -> 8
2. `char s1[20]="Good", s2[]="Day"; strcat(s1,s2); printf("%s",s1);` -> GoodDay
3. `printf("%d", strcmp("Apple","Apple"));` -> 0
4. `char s[]="Hello"; printf("%c", s[1]);` -> e
5. `char s[]="Programming"; printf("%s", s+4);` -> ramming
6. `char s[]="CProgramming"; printf("%.6s", s);` -> CProgr
7. `printf("%d %d", strlen("Mango"), sizeof("Mango"));` -> 5 6
8. `char s[]="John"; for(i=0;i<2;i++) printf("%c",s[i]);` -> Jo
9. `char a[]="Programming"; printf("%s %s", a, a+3);` (approx) -> Programming / ramming
10. `char s[]={'A','B','C','\0'}; printf("%s",s);` -> ABC

## 10 find-the-error questions

1. `char s[3] = "Hello";` (no room, overflow)
2. `strcpy(s, "too long");` into a small array (overflow)
3. `if(s1 == s2)` (address comparison)
4. `printf("%d", strlen(s));` (size_t with %d)
5. `char s[10]; scanf("%[^\n]", s); scanf("%[^\n]", t);` (newline still in buffer)
6. `strcat(s, "x");` with `s` exactly full (overflow)
7. `while(s[i] != NULL)` (NULL is pointer, use `'\0'`)
8. `printf("%s", s[i]);` inside a loop over chars (should be `%c`, `s[i]`)
9. `char *p = "fixed"; p[0] = 'F';` (string literal is read-only - segfault)
10. `gets(s);` (deprecated/removed - buffer overflow; use `fgets`)

## 10 coding problems

1. String length without `strlen` (count until `'\0'`).
2. Copy without `strcpy`.
3. Compare without `strcmp` (walk both, compare chars, check lengths).
4. Concatenate without `strcat`.
5. Count vowels.
6. Reverse a string in place (swap ends).
7. Palindrome check.
8. Convert all lowercase to uppercase.
9. Print only digits.
10. Count words in a sentence.

## 10 MCQs (answers separated below)

1. `strlen("Computer")` a)7 b)8 c)9 d)10 -> **b**
2. `strcat("Good","Day")` a)Good b)Day c)GoodDay d)DayGood -> **c**
3. `strcmp("Apple","Apple")` a)1 b)-1 c)0 d)5 -> **c**
4. `char s[]="Hello"; s[1]` a)H b)e c)l d)o -> **b**
5. Correct string declaration a)`char str[5] = "Hello";` b)`char str[] = "Hello";`
   c)`string str = "Hello";` d)`char str = "Hello";` -> **b**
6. `strchr("There", 'e')` returns pointer to a)T b)h c)e d)r -> **c**
7. `strlen("Mango")` a)4 b)5 c)6 d)7 -> **b**
8. `char s[]="n"; sizeof(s)` a)0 b)1 c)2 d)error -> **c**
9. `char n[]="John"; printf("%s", n);` a)John b)J c)ohn d)error -> **a**
10. `printf("%s %s", "Programming", "Programming"+3)` a)Programming Programming
    b)Programming ramming c)ramming Programming d)error -> **b**

## 5 viva questions

1. Why is the null character important? (Lab-4 Explain Q1)
2. Differentiate strlen, strcpy, strcmp, strcat with examples (Explain Q2).
3. `==` vs `strcmp` for strings (Explain Q3).
4. What is a two-dimensional character array? Declaration + example (Explain Q4).
5. How are strings stored in a 2D char array and what happens when a row
   overflows? (Explain Q5)

## 1 mini project

**Word Counter / Text Analyzer**: read a paragraph, then print - number of
words, characters (with and without spaces), vowels, digits, and the first
letter of each word capitalized. Starting version:
`16-MINI-PROJECTS/code/03_word_counter.c`.
