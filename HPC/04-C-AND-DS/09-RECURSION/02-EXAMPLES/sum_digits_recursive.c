#include <stdio.h>

int digitSum(int n) {
    if(n == 0) return 0;
    return (n % 10) + digitSum(n / 10);
}

int main() {
    printf("Sum of digits of 1234 = %d\n", digitSum(1234));
    printf("Sum of digits of 9999 = %d\n", digitSum(9999));
    return 0;
}
