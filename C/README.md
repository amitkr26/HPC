# C Programs

Practice programs written in C covering basic to intermediate concepts. Every
file begins with a header comment containing the **Question** it solves and its
**Answer** (with sample input/output where applicable).

## Questions and Answers

### Basic I/O and Variables

| Program | Question | Answer / Output |
| --- | --- | --- |
| `hello.c` | Write a C program to print "Hello" and "World". | `printf("Hello\n")` then `printf("World")`. Output: `Hello` then `World`. |
| `age.c` | Declare and initialize variables of different data types (int, char, float) and print their values. | Uses `%c`, `%d`, `%.2f`. Output: `name=R`, `age=25`, `marks=55.90`. |
| `numbers.c` | Accept two numbers from the user and print their sum. | Input `12 30` -> `The sum of your entered numbers is: 42`. |

### Arithmetic and Operators

| Program | Question | Answer / Output |
| --- | --- | --- |
| `binary.c` | Demonstrate binary arithmetic operators on fixed integers `a = 10`, `b = 4`. | `a+b is 14`, `a*b is 40`, `a/b is 2`, `a%b is 2` (`a-b` computed, not printed). |
| `bin.c` | Input two integers and apply `+`, `-`, `*`, `/`, `%`. | Same results as `binary.c` but values come from the user. |
| `operator.c` | Demonstrate pre/post increment and decrement operators. | From `c = 5`: `++c -> 6`, `--c -> 5`, `c-- prints 5`, `c++ prints 4`. |
| `unary.c` | Demonstrate the unary `+` and `-` operators. | `+a` keeps sign, `-b` negates. Input `3 -7` -> `+a = 3`, `-b = 7`. |
| `typecast.c` | Demonstrate a pointer and the `sizeof` operator. | `*ptr` prints `5`; `sizeof(int)` prints `4`. |
| `opera.c` | Simple calculator using `switch` (with division-by-zero protection). | Supports `+ - * /`. Input `10 + 4` -> `Result = 14`; `10 / 0` -> `Cannot divide by zero`. |
| `operators.c` | Simple calculator using `switch`. | Supports `+ - * /`. Input `10 / 4` -> `Result = 2` (no zero check). |
| `test.c` | Evaluate expressions mixing pre/post increments. | `7 12`; `11 19 190`; `6 30` (gcc 6.3.0; some lines are undefined behaviour). |
| `test2.c` | Evaluate `z = x++ * --y` where `x = 10`, `y = 20`. | `x = 11`, `y = 19`, `z = 10 * 19 = 190`. Output: `11 19 190`. |
| `test3.c` | Evaluate `q = ++p * p++` where `p = 4`. | Output (gcc 6.3.0): `6 30` (undefined behaviour). |
| `test4.c` | Evaluate `k = ++i * j--` where `i = 6`, `j = 3`. | `i = 7`, `j = 2`, `k = 21`. |
| `swap.c` | Swap two numbers using a temporary variable. | `temp = num1; num1 = num2; num2 = temp`. Input `5 9` -> `9 5`. |

### Geometry

| Program | Question | Answer / Output |
| --- | --- | --- |
| `area.c` | Find the area of a square. | `area = side * side`. Input `5` -> `25.00`. |
| `circle.c` | Find the area of a circle. | `area = 3.14159 * r * r`. Input `5` -> `78.54`. |
| `circlecir.c` | Find the circumference of a circle. | `circumference = 2 * PI * r` (`PI = 3.14159`). Input `5` -> `31.42`. |

### Decision Making

| Program | Question | Answer / Output |
| --- | --- | --- |
| `even.c` | Check whether a number is even or odd. | `num % 2 == 0` -> Even. Input `8` -> `8 is Even`; `7` -> `7 is Odd`. |
| `div.c` | Check whether a number is divisible by 5. | `num % 5 == 0`. Input `25` -> divisible; `23` -> not divisible. |
| `hot.c` | Print "hot" if the number is greater than 30, else "cold". | Input `35` -> `35 is hot`; `20` -> `20 is cold`. |
| `vote.c` | Check whether a person is an adult or a minor. | `num >= 18` -> Adult. Input `18` -> `18 is Adult`; `15` -> `15 is Minor`. |
| `num.c` | Check whether a number is positive, negative or zero. | `> 0` positive, `== 0` zero, else negative. |
| `leap.c` | Check whether a year is a leap year. | `(year % 400 == 0) || (year % 4 == 0 && year % 100 != 0)`. Input `2024` -> leap; `2023` -> not. |
| `leaps.c` | Check whether a year is a leap year. | Duplicate of `leap.c` with the same rule. |
| `nest.c` | Nested if-else to calculate salary increment by age and salary. | `age >= 30`: 10% (salary <= 500000) else 5%; `age < 30`: 8% (<= 30000) else 3%. |
| `nestedif.c` | Same salary-increment logic as `nest.c` using floating-point math. | Same rules; sample `35 400000` -> new salary `440000.00`. |
| `vowel.c` | Check whether a character is a vowel or consonant using `switch`. | Cases `a e i o u` -> vowel; default -> consonant. |

### Loops

| Program | Question | Answer / Output |
| --- | --- | --- |
| `loop.c` | Show how a `do-while` loop differs from a `while` loop. | `i = 6`; body runs once even though `i <= 5` is false. Output: `6` then `7`. |

## Building

Compile any program with:

```bash
gcc <filename>.c -o <filename>
```

## Topic Map

- Basic I/O and variables: `hello.c`, `age.c`, `numbers.c`
- Operators: `binary.c`, `bin.c`, `operator.c`, `unary.c`, `typecast.c`, `test.c`-`test4.c`, `swap.c`
- Decision making: `even.c`, `div.c`, `hot.c`, `vote.c`, `num.c`, `leap.c`, `leaps.c`, `nest.c`, `nestedif.c`, `vowel.c`
- Switch: `opera.c`, `operators.c`, `vowel.c`
- Loops: `loop.c`
- Geometry: `area.c`, `circle.c`, `circlecir.c`
