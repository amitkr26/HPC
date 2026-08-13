/*
 * Question: Evaluate z = x++ * --y where x = 10 and y = 20.
 * Answer:   x++ uses the old value 10, then increments x to 11.
 *           --y decrements y to 19 before use. z = 10 * 19 = 190.
 *           Output: "11 19 190"
 */
#include <stdio.h>

int main() {
    
    int x =10, y=20,z;
    z=x++ * --y;
    printf("%d %d %d\n", x,y,z);

    return 0;
}