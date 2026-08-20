#include <stdio.h>
#include <math.h>
#define PI 3.14159265358979

float circle(float radius);
float rectangle(float length, float width);
float square(float side);
double power(double x, double y);
double squareRoot(double number);
void displaymenu(void);

int main()
{
    int choice;
    float radius, length, width, side;
    double base, num;

    do
    {
        displaymenu();

        printf("Enter your choice: ");
        scanf("%d", &choice);

        switch (choice)
        {
        case 1:
            printf("Enter radius of the circle: ");
            scanf("%f", &radius);
            if (radius < 0)
                printf("Error: radius cannot be negative.\n");
            else
                printf("Area of circle = %.4f\n", circle(radius));
            break;

        case 2:
            printf("Enter length and width of the rectangle: ");
            scanf("%f %f", &length, &width);
            if (length < 0 || width < 0)
                printf("Error: dimensions cannot be negative.\n");
            else
                printf("Area of rectangle = %.4f\n", rectangle(length, width));
            break;

        case 3:
            printf("Enter side of the square: ");
            scanf("%f", &side);
            if (side < 0)
                printf("Error: side cannot be negative.\n");
            else
                printf("Area of square = %.4f\n", square(side));
            break;

        case 4:
            printf("Enter base and exponent (x y): ");
            scanf("%lf %lf", &base, &num);
            if (num < 0)
                printf("Error: exponent must be non-negative.\n");
            else
                printf("%.2f ^ %.2f = %.4f\n", base, num, power(base, num));
            break;

        case 5:
            printf("Enter a number: ");
            scanf("%lf", &num);
            if (num < 0)
                printf("Error: cannot find square root of a negative number.\n");
            else
                printf("Square root of %.2f = %.4f\n", num, squareRoot(num));
            break;

        case 6:
            printf("Exiting... Thank you!\n");
            break;

        default:
            printf("Invalid choice! Please select a number from 1 to 6.\n");
        }
    } while (choice != 6);

    return 0;
}

float circle(float radius)
{
    return PI * radius * radius;
}

float rectangle(float length, float width)
{
    return length * width;
}

float square(float side)
{
    return side * side;
}

double power(double x, double y)
{
    double result = 1.0;
    int i;
    for (i = 1; i <= y; i++)
        result = result * x;
    return result;
}

double squareRoot(double number)
{
    return sqrt(number);
}

void displaymenu(void)
{
    printf("\n========== CALCULATOR ==========\n");
    printf("1. Area of Circle\n");
    printf("2. Area of Rectangle\n");
    printf("3. Area of Square\n");
    printf("4. Power\n");
    printf("5. Square Root\n");
    printf("6. Exit\n");
}
