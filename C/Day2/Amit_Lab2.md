# Amit_Lab2 - Day 2 Assignment

**C Programming - Lab 2**

---

## Question 1: Check if a number is positive or negative

```c
/*
 * Question: Check if a number is positive or negative.
 */
#include <stdio.h>

int main()
{
    int num;

    printf("Enter a number: ");
    scanf("%d", &num);

    if(num > 0)
    {
        printf("The number %d is positive.\n", num);
    }
    else if(num < 0)
    {
        printf("The number %d is negative.\n", num);
    }
    else
    {
        printf("The number 0 is neither positive nor negative.\n");
    }

    return 0;
}
```

**Output:**

```
Enter a number: -3
The number -3 is negative.
```

---

## Question 2: Check if a number is even or odd

```c
/*
 * Question: Check if a number is even or odd.
 */
#include <stdio.h>

int main()
{
    int num;

    printf("Enter a number: ");
    scanf("%d", &num);

    if(num % 2 == 0)
    {
        printf("%d is even.\n", num);
    }
    else
    {
        printf("%d is odd.\n", num);
    }

    return 0;
}
```

**Output:**

```
Enter a number: 7
7 is odd.
```

---

## Question 3: Check if a person is an adult or minor (18 years)

```c
/*
 * Question: Check if a person is an adult or minor (18 years is the adult age).
 */
#include <stdio.h>

int main()
{
    int age;

    printf("Enter your age: ");
    scanf("%d", &age);

    if(age >= 18)
    {
        printf("You are an adult.\n");
    }
    else
    {
        printf("You are a minor.\n");
    }

    return 0;
}
```

**Output:**

```
Enter your age: 15
You are a minor.
```

---

## Question 4: Check if temperature is hot or cold (30 C or above is Hot)

```c
/*
 * Question: Check if temperature is hot or cold (30 C or above is Hot).
 */
#include <stdio.h>

int main()
{
    int temperature;

    printf("Enter the temperature: ");
    scanf("%d", &temperature);

    if(temperature >= 30)
    {
        printf("Hot\n");
    }
    else
    {
        printf("Cold\n");
    }

    return 0;
}
```

**Output:**

```
Enter the temperature: 35
Hot
```

---

## Question 5: Check if a number is divisible by 5

```c
/*
 * Question: Check if a number is divisible by 5.
 */
#include <stdio.h>

int main()
{
    int num;

    printf("Enter a number: ");
    scanf("%d", &num);

    if(num % 5 == 0)
    {
        printf("%d is divisible by 5.\n", num);
    }
    else
    {
        printf("%d is not divisible by 5.\n", num);
    }

    return 0;
}
```

**Output:**

```
Enter a number: 27
27 is not divisible by 5.
```

---

## Question 6: Maximum of three numbers using Nested-if

```c
/*
 * Question: Find the maximum of three numbers using Nested-if.
 */
#include <stdio.h>

int main()
{
    int a, b, c;

    printf("Enter three numbers: ");
    scanf("%d %d %d", &a, &b, &c);

    if(a > b)
    {
        if(a > c)
        {
            printf("Maximum = %d\n", a);
        }
        else
        {
            printf("Maximum = %d\n", c);
        }
    }
    else
    {
        if(b > c)
        {
            printf("Maximum = %d\n", b);
        }
        else
        {
            printf("Maximum = %d\n", c);
        }
    }

    return 0;
}
```

**Output:**

```
Enter three numbers: 10 20 15
Maximum = 20
```

---

## Question 7: Leap Year using Nested-if

```c
/*
 * Question: Find the Leap Year using Nested-if.
 * A year is a leap year if divisible by 4, except century years,
 * which must be divisible by 400.
 */
#include <stdio.h>

int main()
{
    int year;

    printf("Enter a year: ");
    scanf("%d", &year);

    if(year % 4 == 0)
    {
        if(year % 100 == 0)
        {
            if(year % 400 == 0)
            {
                printf("%d is a leap year.\n", year);
            }
            else
            {
                printf("%d is not a leap year.\n", year);
            }
        }
        else
        {
            printf("%d is a leap year.\n", year);
        }
    }
    else
    {
        printf("%d is not a leap year.\n", year);
    }

    return 0;
}
```

**Output:**

```
Enter a year: 1900
1900 is not a leap year.
```

---

## Question 8: Calculator using switch-case

```c
/*
 * Question: Take two numbers and an operator (+, -, *, /) from the user and
 *           perform the operation using a switch-case statement.
 */
#include <stdio.h>

int main()
{
    int num1, num2;
    char operator;

    printf("Enter first number: ");
    scanf("%d", &num1);

    printf("Enter operator (+, -, *, /): ");
    scanf(" %c", &operator);

    printf("Enter second number: ");
    scanf("%d", &num2);

    switch(operator)
    {
        case '+':
            printf("Result = %d\n", num1 + num2);
            break;

        case '-':
            printf("Result = %d\n", num1 - num2);
            break;

        case '*':
            printf("Result = %d\n", num1 * num2);
            break;

        case '/':
            if(num2 != 0)
            {
                printf("Result = %d\n", num1 / num2);
            }
            else
            {
                printf("Cannot divide by zero\n");
            }
            break;

        default:
            printf("Invalid operator\n");
    }

    return 0;
}
```

**Output:**

```
Enter first number: 10
Enter operator (+, -, *, /): /
Enter second number: 0
Cannot divide by zero
```

---

## Question 9: Vowel or Consonant

```c
/*
 * Question: Check whether a given character is a vowel or a consonant.
 */
#include <stdio.h>

int main()
{
    char ch;

    printf("Enter a character: ");
    scanf(" %c", &ch);

    switch(ch)
    {
        case 'a':
        case 'e':
        case 'i':
        case 'o':
        case 'u':
        case 'A':
        case 'E':
        case 'I':
        case 'O':
        case 'U':
            printf("%c is a vowel.\n", ch);
            break;

        default:
            printf("%c is a consonant.\n", ch);
    }

    return 0;
}
```

**Output:**

```
Enter a character: b
b is a consonant.
```

---

## Question 10: Print numbers from 1 to 10

```c
/*
 * Question: Print numbers from 1 to 10.
 */
#include <stdio.h>

int main()
{
    int i;

    for(i = 1; i <= 10; i++)
    {
        printf("%d ", i);
    }
    printf("\n");

    return 0;
}
```

**Output:**

```
1 2 3 4 5 6 7 8 9 10
```

---

## Question 11: Multiplication table

```c
/*
 * Question: Print the multiplication table of a number.
 */
#include <stdio.h>

int main()
{
    int num, i;

    printf("Enter a number: ");
    scanf("%d", &num);

    for(i = 1; i <= 10; i++)
    {
        printf("%d x %d = %d\n", num, i, num * i);
    }

    return 0;
}
```

**Output:**

```
Enter a number: 5
5 x 1 = 5
5 x 2 = 10
5 x 3 = 15
5 x 4 = 20
5 x 5 = 25
5 x 6 = 30
5 x 7 = 35
5 x 8 = 40
5 x 9 = 45
5 x 10 = 50
```

---

## Question 12: Print even numbers between 1 and 50

```c
/*
 * Question: Print even numbers between 1 and 50.
 */
#include <stdio.h>

int main()
{
    int i;

    for(i = 2; i <= 50; i += 2)
    {
        printf("%d ", i);
    }
    printf("\n");

    return 0;
}
```

**Output:**

```
2 4 6 8 10 12 14 16 18 20 22 24 26 28 30 32 34 36 38 40 42 44 46 48 50
```

---

## Question 13: Numbers divisible by both 3 and 5 (1 to 100)

```c
/*
 * Question: Print only numbers divisible by both 3 and 5 between 1 and 100.
 */
#include <stdio.h>

int main()
{
    int i;

    for(i = 1; i <= 100; i++)
    {
        if(i % 3 == 0 && i % 5 == 0)
        {
            printf("%d ", i);
        }
    }
    printf("\n");

    return 0;
}
```

**Output:**

```
15 30 45 60 75 90
```

---

## Question 14: Sum only odd numbers up to N

```c
/*
 * Question: Sum only odd numbers up to N.
 */
#include <stdio.h>

int main()
{
    int n, i, sum = 0;

    printf("Enter N: ");
    scanf("%d", &n);

    for(i = 1; i <= n; i++)
    {
        if(i % 2 != 0)
        {
            sum += i;
        }
    }

    printf("Sum of odd numbers up to %d = %d\n", n, sum);

    return 0;
}
```

**Output:**

```
Enter N: 5
Sum of odd numbers up to 5 = 9
```

---

## Question 15: Print alphabets from a to z using for loop

```c
/*
 * Question: Print alphabets from a to z using a for loop.
 */
#include <stdio.h>

int main()
{
    char ch;

    for(ch = 'a'; ch <= 'z'; ch++)
    {
        printf("%c ", ch);
    }
    printf("\n");

    return 0;
}
```

**Output:**

```
a b c d e f g h i j k l m n o p q r s t u v w x y z
```

---

## Question 16: Print 5 stars in a row using for loop

```c
/*
 * Question: Print 5 stars (*) in a row using a for loop.
 */
#include <stdio.h>

int main()
{
    int i;

    for(i = 1; i <= 5; i++)
    {
        printf("*");
    }
    printf("\n");

    return 0;
}
```

**Output:**

```
*****
```

---

## Question 17: Square star pattern of N rows

```c
/*
 * Question: Print a square star (*) pattern of N rows using a for loop.
 */
#include <stdio.h>

int main()
{
    int n, row, col;

    printf("Enter number of rows: ");
    scanf("%d", &n);

    for(row = 1; row <= n; row++)
    {
        for(col = 1; col <= n; col++)
        {
            printf("*");
        }
        printf("\n");
    }

    return 0;
}
```

**Output:**

```
Enter number of rows: 3
***
***
***
```

---

## Question 18: Right triangle star pattern

```c
/*
 * Question: Print a right triangle star pattern series using a for loop.
 */
#include <stdio.h>

int main()
{
    int n, row, col;

    printf("Enter number of rows: ");
    scanf("%d", &n);

    for(row = 1; row <= n; row++)
    {
        for(col = 1; col <= row; col++)
        {
            printf("*");
        }
        printf("\n");
    }

    return 0;
}
```

**Output:**

```
Enter number of rows: 5
*
**
***
****
*****
```

---

## Question 19: Print stars in a row using while loop (user input)

```c
/*
 * Question: Print stars (*) in a row by getting user input using a while loop.
 */
#include <stdio.h>

int main()
{
    int n, i = 0;

    printf("Enter number of stars: ");
    scanf("%d", &n);

    while(i < n)
    {
        printf("*");
        i++;
    }
    printf("\n");

    return 0;
}
```

**Output:**

```
Enter number of stars: 5
*****
```

---

## Question 20: Print stars in a row using while loop (user input)

```c
/*
 * Question: Print stars (*) in a row by getting user input using a while loop.
 * Note: Question 19 and Question 20 are identical in the assignment sheet.
 */
#include <stdio.h>

int main()
{
    int n, i = 0;

    printf("Enter number of stars: ");
    scanf("%d", &n);

    while(i < n)
    {
        printf("*");
        i++;
    }
    printf("\n");

    return 0;
}
```

**Output:**

```
Enter number of stars: 7
*******
```

---

## Bonus: Simple ATM Machine (if...else only)

```c
/*
 * Question: Simulate a simple ATM machine using only if...else statements.
 * - Ask for a 4-digit PIN (correct PIN: 1234) -> show menu.
 * - Wrong PIN -> "Access Denied" and end.
 * - Menu: 1. Check Balance  2. Withdraw Money  3. Deposit Money
 * - Any other choice -> "Invalid choice".
 * - Print a thank-you message before ending.
 */
#include <stdio.h>

int main()
{
    int pin, choice;
    float balance = 5000.0, amount;

    printf("Enter your 4-digit PIN: ");
    scanf("%d", &pin);

    if(pin == 1234)
    {
        printf("\nWelcome!\n");
        printf("1. Check Balance\n");
        printf("2. Withdraw Money\n");
        printf("3. Deposit Money\n");
        printf("Enter your choice: ");
        scanf("%d", &choice);

        if(choice == 1)
        {
            printf("Your current balance is: %.2f\n", balance);
        }
        else if(choice == 2)
        {
            printf("Enter amount to withdraw: ");
            scanf("%f", &amount);

            if(amount <= balance)
            {
                balance = balance - amount;
                printf("Withdrawal successful. New balance: %.2f\n", balance);
            }
            else
            {
                printf("Insufficient balance.\n");
            }
        }
        else if(choice == 3)
        {
            printf("Enter amount to deposit: ");
            scanf("%f", &amount);

            balance = balance + amount;
            printf("Deposit successful. New balance: %.2f\n", balance);
        }
        else
        {
            printf("Invalid choice.\n");
        }
    }
    else
    {
        printf("Access Denied\n");
    }

    printf("Thank you for using our ATM.\n");

    return 0;
}
```

**Output (withdraw):**

```
Enter your 4-digit PIN: 1234

Welcome!
1. Check Balance
2. Withdraw Money
3. Deposit Money
Enter your choice: 2
Enter amount to withdraw: 2000
Withdrawal successful. New balance: 3000.00
Thank you for using our ATM.
```

**Output (wrong PIN):**

```
Enter your 4-digit PIN: 9999
Access Denied
Thank you for using our ATM.
```

---

## Question Bank: Answers

| Q | Answer | Explanation |
|---|--------|-------------|
| 1 | **A. Greater than 5** | `10 > 5` is true |
| 2 | **A. 5 4 3 2 1** | `i` decrements from 5 to 1 |
| 3 | **B. 0 1 2 4** | `continue` at `i==3` skips printing 3 |
| 4 | **B. 0 1 2** | `break` at `i==3` exits the loop |
| 5 | **C. 1 2 3** | `goto` loops until `i` becomes 4 |
| 6 | **b. Two** | first `else if` matches; second `else if(x==2)` is never reached |
| 7 | **B. 0 1** | after `i==2`, `flag` stays 1, so `continue` skips 2, 3, 4 |
| 8 | **B. 1 2 4 5** | post-increment `count++`; `continue` at `count==3` |

## Question Bank: Grade Program

```c
/*
 * Question: Take a student's marks as input and assign a grade using an
 *           else-if ladder:
 *           90-100 -> Grade A
 *           75-89  -> Grade B
 *           50-74  -> Grade C
 *           35-49  -> Grade D
 *           Below 35 -> Fail
 */
#include <stdio.h>

int main()
{
    int marks;

    printf("Enter the student's marks: ");
    scanf("%d", &marks);

    if(marks >= 90 && marks <= 100)
    {
        printf("Grade A\n");
    }
    else if(marks >= 75 && marks <= 89)
    {
        printf("Grade B\n");
    }
    else if(marks >= 50 && marks <= 74)
    {
        printf("Grade C\n");
    }
    else if(marks >= 35 && marks <= 49)
    {
        printf("Grade D\n");
    }
    else
    {
        printf("Fail\n");
    }

    return 0;
}
```

**Output:**

```
Enter the student's marks: 92
Grade A
```

---

## Conceptual Questions

**1. Which loop should be used when the number of iterations is known in advance? Why?**

The **for loop**. Because when the number of iterations is known, everything can be written in one line: the initialization, the condition, and the increment, e.g. `for(i = 1; i <= 10; i++)`.

**2. Which loop is suitable when the number of iterations is not known in advance? Explain with an example.**

The **while loop**. It checks the condition before running the body, so it is used when the loop depends on conditions that change at runtime. Example: keep reading numbers until the user enters -1.

```c
int num;
printf("Enter numbers (-1 to stop): ");
scanf("%d", &num);
while(num != -1)
{
    printf("%d\n", num);
    scanf("%d", &num);
}
```

**3. Which loop guarantees that its body executes at least once? Why?**

The **do-while loop**. Because it checks the condition at the end, after the body has already run once.

**4. What is the difference between entry-controlled and exit-controlled loops?**

Entry-controlled loops (**for**, **while**) test the condition before entering the body, so the body may execute zero times. Exit-controlled loops (**do-while**) test the condition after the body, so the body executes at least once.

**5. Why is a semicolon required after the condition in a do-while loop?**

The semicolon terminates the `while(condition);` statement. It is part of the do-while syntax that tells the compiler where the loop ends.

**6. What is the difference between break and continue in C?**

`break` immediately exits the loop (or switch) entirely and continues after it. `continue` skips the rest of the current iteration and jumps to the next iteration of the loop.

**7. Can a switch statement completely replace an if-else statement in every situation? Explain.**

No. `switch` can only compare a value for equality against constant integer/character values. It cannot handle ranges, relational conditions, floating-point values, or compound boolean conditions. `if-else` is more flexible and can replace `switch`, but not the other way around.

**8. What types of values can generally be used with case labels?**

Case labels must be constant expressions of integer type: `int`, `char`, or `enum` values. Floating-point values, variables, and strings are not allowed.

**9. What is the purpose of the sizeof operator in C? Does sizeof return the size in bits or bytes?**

`sizeof` returns the memory size of a type or variable in **bytes** (not bits). Example: `sizeof(int)` usually returns 4 on most systems.

**10. How many times will the inner statement execute?**

```c
for(i = 1; i <= 3; i++)
{
    for(j = 1; j <= 4; j++)
    {
        printf("*");
    }
}
```

**12 times.** The outer loop runs 3 times and the inner loop runs 4 times each time: `3 x 4 = 12`.
