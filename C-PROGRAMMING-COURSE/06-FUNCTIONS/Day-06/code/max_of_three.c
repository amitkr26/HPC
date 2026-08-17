#include <stdio.h>

int maxOfThree(int a, int b, int c) {
    int max = a;
    if(b > max) max = b;
    if(c > max) max = c;
    return max;
}

int main() {
    printf("Max of 10, 20, 15 = %d\n", maxOfThree(10, 20, 15));
    return 0;
}
