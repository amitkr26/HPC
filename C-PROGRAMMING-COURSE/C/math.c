#include <stdio.h>
#include<math.h>


int main()
{
    float num, a, b;

    printf("Enter a number: ");
    scanf("%f", &num);
    printf("a: ");
    scanf("%f", &a);
    printf("b: ");
    scanf("%f", &b);
    printf("The suareroot of number is: %f\n", sqrt(num));
    printf("The ceil of a: %f\n", ceil(a));
    printf("The floor of b: %f\n", floor(b));
    printf("The cube of number is: %f\n", pow(num, 3));

    return 0;
}