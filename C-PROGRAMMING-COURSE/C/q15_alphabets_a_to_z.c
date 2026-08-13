/*
 * Question: Print alphabets from a to z using a for loop.
 * Answer:   Output: a b c d e f ... x y z
 */
#include <stdio.h>

int main()
{
    char ch;

    for(ch = 'a'; ch <= 'z'; ch++)
    {
        printf("%c ", ch);
    }
    printf("\n");

    return 0;
}
