/*
 * Question: Write a C program to find the area of a circle.
 * Answer:   area = 3.14159 * radius * radius.
 *           Sample Input: 5 -> Output: Area of the circle = 78.54
 */
#include <stdio.h>

int main() {
    float radius, area;

    printf("Enter the radius: ");
    scanf("%f", &radius);

    area = 3.14159 * radius * radius;

    printf("Area of the circle = %.2f\n", area);

    return 0;
}