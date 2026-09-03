/*
 * Word Counter / Text Analyzer
 *
 * Reads a line of text and reports:
 *   - number of words
 *   - total characters (excluding the newline)
 *   - characters without spaces
 *   - number of vowels
 *   - number of digits
 * Then prints the line with every word's first letter capitalized.
 *
 * Concepts: fgets, ctype.h (isalpha, isdigit, toupper), loops.
 * Built on: Day 4 (strings and character classification).
 */
#include <stdio.h>
#include <ctype.h>

int main()
{
    char text[200];
    int words = 0, chars = 0, noSpace = 0, vowels = 0, digits = 0;
    int i, inWord = 0, capitalNext = 1;

    printf("Enter a line of text: ");
    fgets(text, sizeof(text), stdin);

    for (i = 0; text[i] != '\0'; i++)
    {
        char ch = text[i];

        if (ch == '\n')
        {
            continue;    /* do not count the newline */
        }

        chars++;                      /* every real character */

        if (ch == ' ')
        {
            inWord = 0;               /* a space ends the current word */
            capitalNext = 1;          /* next letter should be capital */
            continue;
        }

        noSpace++;

        if (isalpha(ch))
        {
            /* Capitalize the first letter of each word. */
            if (capitalNext)
            {
                text[i] = (char)toupper(ch);
                capitalNext = 0;
            }

            /* Check vowels (both cases). */
            if (ch == 'a' || ch == 'A' || ch == 'e' || ch == 'E' ||
                ch == 'i' || ch == 'I' || ch == 'o' || ch == 'O' ||
                ch == 'u' || ch == 'U')
            {
                vowels++;
            }
        }
        else if (isdigit(ch))
        {
            digits++;
        }

        /* A non-space character starts (or continues) a word. */
        if (!inWord)
        {
            words++;
            inWord = 1;
        }
    }

    printf("\nResults:\n");
    printf("Words: %d\n", words);
    printf("Total characters (without newline): %d\n", chars);
    printf("Characters without spaces: %d\n", noSpace);
    printf("Vowels: %d\n", vowels);
    printf("Digits: %d\n", digits);

    printf("Capitalized: %s\n", text);

    return 0;
}
