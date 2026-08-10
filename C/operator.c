/*
 * Question: Demonstrate the effect of pre/post increment (++) and decrement
 *           (--) operators on a variable.
 * Answer:   Starting with c = 5:
 *           ++c -> 6, --c -> 5, c-- prints 5 (then c = 4), c++ prints 4 (then c = 5).
 */
#include <stdio.h>

int main() {
    int c=5;
    printf("c = %d\n", c); //5
    printf("++c = %d\n", ++c); // 6
    printf("--c = %d\n", --c); //5
    printf("c-- = %d\n", c--); //5
    printf("c++ = %d\n", c++); //4
    printf("c = %d", c); //5
    return 0;
}