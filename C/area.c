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