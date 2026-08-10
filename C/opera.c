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