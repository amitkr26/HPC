#include<stdio.h>

int main()
{
    int num1, num2;
    
    printf("Enter two numbers: ");
    scanf("%d %d", &num1, &num2);
    printf("Your entered numbers are: %d and %d\n", num1, num2);
    
    int sum;
    sum = num1+num2;
    printf("The sum of your entered numbers is: %d", sum);

    return 0;
}