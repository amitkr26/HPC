/*
 * Question: Write a C program using the switch statement to check whether a
 *           character is a vowel or a consonant.
 * Answer:   Cases a, e, i, o, u -> vowel; default -> consonant.
 *           Input a -> "a is a vowel"; Input b -> "b is a consonant"
 */
#include <stdio.h>

int main()
{
    char ch;

    printf("Enter a character: ");
    scanf(" %c", &ch);

    switch(ch)
    {
        case 'a':
        printf("%c is a vowel\n", ch);
        break;
        case 'e':
        printf("%c is a vowel\n", ch);
        break;
        case 'i':
        printf("%c is a vowel\n", ch);
        break;
        case 'o':
        printf("%c is a vowel\n", ch);
        break;
        case 'u':
            printf("%c is a vowel\n", ch);
            break;

        default:
            printf("%c is a consonant\n", ch);
    }

    return 0;
}