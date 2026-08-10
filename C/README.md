# C Programs

Practice programs written in C covering basic to intermediate concepts. The
programs are organized into **modules by programming level**. Every file begins
with a header comment containing the **Question** it solves and its **Answer**
(with sample input/output where applicable).

## Modules

```
C/
├── Beginner/       Basic I/O, variables, arithmetic, simple if-else, loops
├── Intermediate/   switch, nested if, increment/decrement, pointers
└── Advanced/       Complex expressions and undefined behaviour
```

## Module: Beginner

Programs that introduce I/O, variables, operators and simple decision making.

| Program | Question | Answer / Output |
| --- | --- | --- |
| `hello.c` | Print "Hello" and "World". | `printf("Hello\n")` then `printf("World")`. |
| `age.c` | Declare and print variables of different data types. | `%c`, `%d`, `%.2f`. Output: `name=R`, `age=25`, `marks=55.90`. |
| `numbers.c` | Accept two numbers and print their sum. | Input `12 30` -> `The sum of your entered numbers is: 42`. |
| `binary.c` | Demonstrate binary arithmetic on fixed integers. | `a+b is 14`, `a*b is 40`, `a/b is 2`, `a%b is 2`. |
| `bin.c` | Apply `+ - * / %` to two user-input integers. | Same as `binary.c` with user input. |
| `unary.c` | Demonstrate the unary `+` and `-` operators. | `+a` keeps sign, `-b` negates. |
| `swap.c` | Swap two numbers using a temporary variable. | Input `5 9` -> `9 5`. |
| `area.c` | Find the area of a square. | `area = side * side`. Input `5` -> `25.00`. |
| `circle.c` | Find the area of a circle. | `area = 3.14159 * r * r`. Input `5` -> `78.54`. |
| `circlecir.c` | Find the circumference of a circle. | `2 * PI * r`. Input `5` -> `31.42`. |
| `even.c` | Check whether a number is even or odd. | `num % 2 == 0` -> Even. |
| `div.c` | Check whether a number is divisible by 5. | `num % 5 == 0`. |
| `hot.c` | Print "hot" if number > 30, else "cold". | Input `35` -> hot; `20` -> cold. |
| `vote.c` | Check whether a person is an adult or a minor. | `num >= 18` -> Adult. |
| `num.c` | Check whether a number is positive, negative or zero. | `> 0` positive, `== 0` zero, else negative. |
| `loop.c` | Show how `do-while` differs from `while`. | Output: `6` then `7`. |

## Module: Intermediate

Programs that use `switch`, nested `if-else`, increment/decrement operator
sequences, and pointers.

| Program | Question | Answer / Output |
| --- | --- | --- |
| `leap.c` | Check whether a year is a leap year. | `(year % 400 == 0) || (year % 4 == 0 && year % 100 != 0)`. |
| `leaps.c` | Check whether a year is a leap year. | Duplicate of `leap.c`. |
| `operator.c` | Demonstrate pre/post increment and decrement. | From `c = 5`: `++c -> 6`, `--c -> 5`, `c-- prints 5`, `c++ prints 4`. |
| `opera.c` | Simple calculator using `switch` (zero-safe). | Supports `+ - * /`. `10 + 4` -> `14`; `10 / 0` -> `Cannot divide by zero`. |
| `operators.c` | Simple calculator using `switch`. | Supports `+ - * /`. Input `10 / 4` -> `Result = 2`. |
| `vowel.c` | Check vowel or consonant using `switch`. | Cases `a e i o u` -> vowel; default -> consonant. |
| `nest.c` | Nested if-else salary increment by age and salary. | `age >= 30`: 10% (<=500000) else 5%; else 8% (<=30000) else 3%. |
| `nestedif.c` | Same salary logic using floating-point math. | Input `35 400000` -> new salary `440000.00`. |
| `typecast.c` | Demonstrate a pointer and `sizeof`. | `*ptr` prints `5`; `sizeof(int)` prints `4`. |
| `test2.c` | Evaluate `z = x++ * --y` where `x = 10`, `y = 20`. | `11 19 190` (`z = 10 * 19`). |
| `test4.c` | Evaluate `k = ++i * j--` where `i = 6`, `j = 3`. | `i = 7`, `j = 2`, `k = 21`. |

## Module: Advanced

Programs that combine operators in ways that rely on evaluation order or
trigger undefined behaviour.

| Program | Question | Answer / Output |
| --- | --- | --- |
| `test.c` | Evaluate expressions mixing pre/post increments. | `7 12`; `11 19 190`; `6 30` (gcc 6.3.0; some lines are undefined behaviour). |
| `test3.c` | Evaluate `q = ++p * p++` where `p = 4`. | Output (gcc 6.3.0): `6 30` (undefined behaviour). |

## Building

Compile any program with:

```bash
gcc <module>/<filename>.c -o <module>/<filename>
```

## Topic Map

- **Basic I/O and variables:** `hello.c`, `age.c`, `numbers.c`
- **Arithmetic operators:** `binary.c`, `bin.c`, `unary.c`, `swap.c`
- **Geometry:** `area.c`, `circle.c`, `circlecir.c`
- **Decision making:** `even.c`, `div.c`, `hot.c`, `vote.c`, `num.c`, `leap.c`, `leaps.c`, `nest.c`, `nestedif.c`
- **Switch:** `opera.c`, `operators.c`, `vowel.c`
- **Loops:** `loop.c`
- **Increment/decrement operators:** `operator.c`, `test2.c`, `test4.c`, `test.c`, `test3.c`
- **Pointers:** `typecast.c`
