/*
 * Question: Write a C program to check whether a number is positive, negative
 *           or zero.
 * Answer:   num > 0 -> positive; num == 0 -> zero; otherwise negative.
 *           Input 5 -> "5 is positive"; 0 -> "0 is zero"; -5 -> "-5 is negative"
 */
#include<stdio.h>

int main()
{
    int num;
    printf("Enter a number ");
    scanf("%d", &num);
    
    if(num>0)
    {
        printf("%d is positive\n", num);
    }
    else if(num==0)
    {
        printf("%d is zero\n", num);
    }
    else{
        printf("%d is negative\n", num);
    }

    return 0;
}