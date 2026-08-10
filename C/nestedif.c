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