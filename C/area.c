/*
 * Question: Write a C program to find the area of a square.
 * Answer:   area = side * side.
 *           Sample Input: 5 -> Output: The area of square is: 25.00
 */
#include<stdio.h>

int main()
{
    float side, area;
    printf("Side of the square: ");
    scanf("%f", &side);
    area = (side*side);
    printf("The area of square is: %.2f\n", area);

    return 0;
}