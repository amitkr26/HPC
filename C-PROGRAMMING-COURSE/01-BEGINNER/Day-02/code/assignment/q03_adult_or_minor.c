/*
 * Question: Check if a person is an adult or minor (18 years is the adult age).
 * Answer:   Input 20 -> "You are an adult."
 *           Input 15 -> "You are a minor."
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
