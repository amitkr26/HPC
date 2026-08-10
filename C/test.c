#include <stdio.h>

int main() {
    int a=5, b;
    b = a++ + ++a;
    printf("%d %d\n", a,b);

    int x =10, y=20,z;
    z=x++ * --y;
    printf("%d %d %d\n", x,y,z);

    int p=4,q;
    q= ++p * p++;
    printf("%d %d", p,q);

    return 0;
}