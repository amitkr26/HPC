#include <stdio.h>

int main() {
    int a, b;
    printf("Enter the value of a and b: ");
    scanf("%d %d", &a, &b);
    printf("Your Entered number (a):%d -> Unary operation (+a):%d\n", a,+a);
    printf("Your Entered number (b):%d -> Unary operation (-b):%d\n", a,-b);

    return 0;
}