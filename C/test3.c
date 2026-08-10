/*
 * Question: Evaluate q = ++p * p++ where p = 4.
 * Answer:   Output produced by gcc 6.3.0: "6 30" (p becomes 6, q = 6 * 5).
 *           Note: p is modified twice between sequence points, which is
 *           undefined behaviour in C; output may vary by compiler.
 */
#include <stdio.h>

int main() {

    int p=4,q;
    q= ++p * p++;
    printf("%d %d", p,q);

    return 0;
}