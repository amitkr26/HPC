#include <stdio.h>
#include <math.h>

float areaCircle(float r)
{
    return 3.14159 * r * r;
}

float areaRectangle(float l, float w)
{
    return l * w;
}

float areaSquare(float s)
{
    return s * s;
}

double power(double base, double exp)
{
    return pow(base, exp);
}

double squareRoot(double n)
{
    return sqrt(n);
}

int main()
{
    int choice;
    float radius, length, width, side;
    double base, exp, num;

    do
    {
        printf("\n===== MENU-DRIVEN CALCULATOR =====\n");
        printf("1. Area of Circle\n");
        printf("2. Area of Rectangle\n");
        printf("3. Area of Square\n");
        printf("4. Power (x^y)\n");
        printf("5. Square Root\n");
        printf("6. Exit\n");
        printf("Enter your choice: ");
        scanf("%d", &choice);

        switch (choice)
        {
        case 1:
            printf("Enter radius: ");
            scanf("%f", &radius);
            printf("Area of circle = %.2f\n", areaCircle(radius));
            break;
        case 2:
            printf("Enter length and width: ");
            scanf("%f %f", &length, &width);
            printf("Area of rectangle = %.2f\n", areaRectangle(length, width));
            break;
        case 3:
            printf("Enter side: ");
            scanf("%f", &side);
            printf("Area of square = %.2f\n", areaSquare(side));
            break;
        case 4:
            printf("Enter base and exponent: ");
            scanf("%lf %lf", &base, &exp);
            printf("%.2lf ^ %.2lf = %.2lf\n", base, exp, power(base, exp));
            break;
        case 5:
            printf("Enter a number: ");
            scanf("%lf", &num);
            if (num < 0)
                printf("Error: square root of a negative number is not defined.\n");
            else
                printf("Square root of %.2lf = %.2lf\n", num, squareRoot(num));
            break;
        case 6:
            printf("Exiting... Thank you!\n");
            break;
        default:
            printf("Invalid choice! Please select a number from the menu.\n");
        }
    } while (choice != 6);

    return 0;
}