#include <stdio.h>

int reverse(int n, int rev)
{
    if (n == 0)
    {
        return rev;
    }

    rev = rev * 10 + n % 10;

    return reverse(n / 10, rev);
}

int main()
{
    int n, result;

    printf("Enter a number: ");
    scanf("%d", &n);

    result = reverse(n, 0);

    printf("Reverse = %d\n", result);

    return 0;
}