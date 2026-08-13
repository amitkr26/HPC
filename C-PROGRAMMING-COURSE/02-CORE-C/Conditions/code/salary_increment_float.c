/*
 * Question: Write a C program using nested if-else to calculate a salary
 *           increment based on age and salary (floating-point version).
 * Answer:   Same rules as nest.c but computed with floating-point values:
 *           age >= 30: 10% (salary <= 500000) else 5%.
 *           age < 30 : 8% (salary <= 30000) else 3%.
 *           Input 35 400000 -> increment 40000, new salary 440000.00
 */
#include <stdio.h>

int main()
{
    int age, salary;

    printf("Enter your age: ");
    scanf("%d", &age);

    printf("Enter your salary: ");
    scanf("%d", &salary);

    if(age >= 30)
    {
        if(salary <= 500000)
        {
            printf("You get a 10%% increment.\n");
            printf("Increment amount: %.f\n", salary * 0.10);
            printf("New salary is: %.2f\n", salary + salary * 0.10);
        }
        else
        {
            printf("You get a 5%% increment.\n");
            printf("Increment amount: %.2f\n", salary * 0.05);
            printf("New salary is: %.2f\n", salary + salary * 0.05);
        }
    }
    else
    {
        if(salary <= 30000)
        {
            printf("You get an 8%% increment.\n");
            printf("Increment amount: %.2f\n", salary * 0.08);
            printf("New salary is: %.2f\n", salary + salary * 0.08);
        }
        else
        {
            printf("You get a 3%% increment.\n");
            printf("Increment amount: %.2f\n", salary * 0.03);
            printf("New salary is: %.2f\n", salary + salary * 0.03);
        }
    }

    return 0;
}