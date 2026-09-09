#include <stdio.h>
#include <math.h>

double area_circle(double radius) {
    return M_PI * radius * radius;
}

double area_rectangle(double length, double width) {
    return length * width;
}

double area_square(double side) {
    return side * side;
}

double power(double base, double exponent) {
    return pow(base, exponent);
}

double square_root(double num) {
    if (num < 0) {
        return NAN;
    }
    return sqrt(num);
}

void display_menu() {
    printf("\n=== Menu-Driven Calculator ===\n");
    printf("1. Calculate Area of Circle\n");
    printf("2. Calculate Area of Rectangle\n");
    printf("3. Calculate Area of Square\n");
    printf("4. Calculate Power (x^y)\n");
    printf("5. Calculate Square Root\n");
    printf("6. Exit\n");
    printf("Enter your choice (1-6): ");
}

int main() {
    int choice;
    double radius, length, width, side, base, exponent, num, result;

    do {
        display_menu();
        if (scanf("%d", &choice) != 1) {
            printf("Invalid input! Please enter a number between 1 and 6.\n");
            while (getchar() != '\n');
            continue;
        }

        switch (choice) {
            case 1:
                printf("Enter radius: ");
                if (scanf("%lf", &radius) != 1 || radius < 0) {
                    printf("Invalid radius! Please enter a non-negative number.\n");
                    while (getchar() != '\n');
                    break;
                }
                result = area_circle(radius);
                printf("Area of circle = %.2f\n", result);
                break;

            case 2:
                printf("Enter length: ");
                if (scanf("%lf", &length) != 1 || length < 0) {
                    printf("Invalid length! Please enter a non-negative number.\n");
                    while (getchar() != '\n');
                    break;
                }
                printf("Enter width: ");
                if (scanf("%lf", &width) != 1 || width < 0) {
                    printf("Invalid width! Please enter a non-negative number.\n");
                    while (getchar() != '\n');
                    break;
                }
                result = area_rectangle(length, width);
                printf("Area of rectangle = %.2f\n", result);
                break;

            case 3:
                printf("Enter side length: ");
                if (scanf("%lf", &side) != 1 || side < 0) {
                    printf("Invalid side! Please enter a non-negative number.\n");
                    while (getchar() != '\n');
                    break;
                }
                result = area_square(side);
                printf("Area of square = %.2f\n", result);
                break;

            case 4:
                printf("Enter base: ");
                if (scanf("%lf", &base) != 1) {
                    printf("Invalid base!\n");
                    while (getchar() != '\n');
                    break;
                }
                printf("Enter exponent: ");
                if (scanf("%lf", &exponent) != 1) {
                    printf("Invalid exponent!\n");
                    while (getchar() != '\n');
                    break;
                }
                result = power(base, exponent);
                printf("Result = %.2f\n", result);
                break;

            case 5:
                printf("Enter number: ");
                if (scanf("%lf", &num) != 1) {
                    printf("Invalid input!\n");
                    while (getchar() != '\n');
                    break;
                }
                result = square_root(num);
                if (isnan(result)) {
                    printf("Error: Cannot calculate square root of negative number!\n");
                } else {
                    printf("Square root = %.2f\n", result);
                }
                break;

            case 6:
                printf("Exiting program. Goodbye!\n");
                break;

            default:
                printf("Invalid choice! Please select a number between 1 and 6.\n");
        }
    } while (choice != 6);

    return 0;
}