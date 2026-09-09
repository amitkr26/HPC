/*
 * Question: Evaluate the output of expressions that mix pre/post increment
 *           operators.
 * Answer:   Output produced by gcc 6.3.0:
 *           b = a++ + ++a (a = 5)  -> "7 12"
 *           z = x++ * --y (10, 20) -> "11 19 190"
 *           q = ++p * p++ (p = 4)  -> "6 30"
 *           Note: some of these expressions modify the same variable between
 *           two sequence points, which is undefined behaviour in C; results
 *           may differ between compilers.
 */
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