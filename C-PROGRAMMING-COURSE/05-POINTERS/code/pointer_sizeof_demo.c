/*
 * Question: Write a C program to demonstrate a pointer and the sizeof operator.
 * Answer:   ptr is assigned the address of a; *ptr prints 5, and sizeof(int)
 *           prints 4 (typical 32-bit int).
 *           Output: 5, size of integer: 4
 */
#include<stdio.h>
int main()
{
    int a=5;
    int *ptr;
    ptr = &a;
    printf("%d\n", *ptr);
    printf("size of integer: %d", sizeof(int));

    return 0;
}