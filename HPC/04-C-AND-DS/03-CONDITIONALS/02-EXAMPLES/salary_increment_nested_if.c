/*
 * Question: Write a C program using nested if-else to calculate a salary
 *           increment based on age and current salary.
 * Answer:   age >= 30: salary <= 500000 -> 10% increment, else 5%.
 *           age < 30 : salary <= 30000  -> 8% increment, else 3%.
 *           Input 35 400000 -> 10% increment, amount 40000, new salary 440000.
 */
#include <stdio.h>

int main()
{
    int age, salary;
    int increment, newSalary;

    printf("Enter your age: ");
    scanf("%d", &age);

    printf("Enter your salary: ");
    scanf("%d", &salary);

    if(age >= 30)
    {
        if(salary <= 500000)
        {
            increment = salary * 10 / 100;
            newSalary = salary + increment;

            printf("You get a 10%% increment.\n");
            printf("Increment amount: %d\n", increment);
            printf("New salary is: %d\n", newSalary);
        }
        else
        {
            increment = salary * 5 / 100;
            newSalary = salary + increment;

            printf("You get a 5%% increment.\n");
            printf("Increment amount: %d\n", increment);
            printf("New salary is: %d\n", newSalary);
        }
    }
    else
    {
        if(salary <= 30000)
        {
            increment = salary * 8 / 100;
            newSalary = salary + increment;

            printf("You get an 8%% increment.\n");
            printf("Increment amount: %d\n", increment);
            printf("New salary is: %d\n", newSalary);
        }
        else
        {
            increment = salary * 3 / 100;
            newSalary = salary + increment;

            printf("You get a 3%% increment.\n");
            printf("Increment amount: %d\n", increment);
            printf("New salary is: %d\n", newSalary);
        }
    }

    return 0;
}