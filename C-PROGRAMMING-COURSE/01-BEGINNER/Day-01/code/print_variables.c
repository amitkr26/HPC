/*
 * Question: Write a C program to declare and initialize variables of different
 *           data types (int, char, float) and print their values.
 * Answer:   Uses %c for char, %d for int and %.2f for float.
 *           Output: name=R, age=25, marks=55.90
 */
#include<stdio.h>
int main()
{
    int age = 25;
    char name= 'R';
    float marks = 55.9;

    printf("name=%c\n", name);
    printf("age=%d\n", age);
    printf("marks=%.2f\n", marks);
    return 0;
}