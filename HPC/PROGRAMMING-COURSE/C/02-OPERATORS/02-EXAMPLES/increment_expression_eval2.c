/*
 * Question: Evaluate k = ++i * j-- where i = 6 and j = 3.
 * Answer:   ++i makes i = 7 before use; j-- uses the old value 3, then
 *           decrements j to 2. k = 7 * 3 = 21.
 *           Output: i = 7, j = 2, k = 21
 */
#include <stdio.h>

int main()
{
    int i = 6, j = 3, k;

    k = ++i * j--;

    printf("i = %d\n", i);
    printf("j = %d\n", j);
    printf("k = %d\n", k);

    return 0;
}