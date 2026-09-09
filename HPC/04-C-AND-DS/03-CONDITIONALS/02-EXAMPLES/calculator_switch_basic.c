/*
 * Question: Write a C program to create a simple calculator using the switch
 *           statement.
 * Answer:   Supports +, -, *, /.
 *           Sample Input: 10 / 4 -> "Result = 2"
 *           Note: unlike calculator_switch_safe.c, this version does not check
 *           for division by zero.
 */
#include <stdio.h>

int main()
{
    int a, b;
    char op;

    printf("Enter first number: ");
    scanf("%d", &a);

    printf("Enter operator (+, -, *, /): ");
    scanf(" %c", &op);

    printf("Enter second number: ");
    scanf("%d", &b);

    switch(op)
    {
        case '+':
            printf("Result = %d\n", a+b);
            break;

        case '-':
            printf("Result = %d\n", a-b);
            break;

        case '*':
            printf("Result = %d\n", a*b);
            break;

        case '/':
           printf("Result = %d\n", a/b);
            break;

        default:
            printf("Enter a valid operator\n");
    }

    return 0;
}