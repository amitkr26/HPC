/* Q9. Accept a string. Define a vowel array containing lowercase and uppercase
       vowels. Iterate through each character and compare it against the vowel
       array. Print each character from the input string that is a vowel,
       followed by a space. */
#include <stdio.h>
#include <string.h>

int main()
{
    char str[100];
    char vowels[] = {'a', 'e', 'i', 'o', 'u', 'A', 'E', 'I', 'O', 'U'};
    int i, j;

    printf("Enter a string: ");
    fgets(str, sizeof(str), stdin);
    str[strcspn(str, "\n")] = '\0';

    printf("Vowels in the string: ");
    for (i = 0; str[i] != '\0'; i++)
    {
        for (j = 0; j < 10; j++)
        {
            if (str[i] == vowels[j])
            {
                printf("%c ", str[i]);
                break;
            }
        }
    }
    printf("\n");

    return 0;
}
