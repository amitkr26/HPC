/*
 * Question: Demonstrate how a do-while loop differs from a while loop.
 * Answer:   i starts at 6. A do-while loop always executes its body at least
 *           once, so 6 is printed even though the condition (i <= 5) is false.
 *           After the loop i is 7.
 *           Output:
 *           6
 *           7
 */
#include <stdio.h>

int main()
{
    int i = 6;

    do
    {
        printf("%d\n", i);
        ++i;
    }
    while(i <= 5);
    printf("%d\n", i);

    return 0;
}