/*
 * Question: Write a C program to find the circumference of a circle.
 * Answer:   circumference = 2 * PI * radius, where PI is defined as 3.14159.
 *           Sample Input: 5 -> Output: Circumference of the circle = 31.42
 */
#include <stdio.h>

#define PI 3.14159

int main() {
    float radius, circumference;

    printf("Enter the radius: ");
    scanf("%f", &radius);

    circumference = 2 * PI * radius;

    printf("Circumference of the circle = %.2f\n", circumference);

    return 0;
}