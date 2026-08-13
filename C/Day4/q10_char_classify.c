/* Q10. Accept a string, then print each character one by one while also
        identifying whether it is a lowercase letter, an uppercase letter,
        a digit, or a special character. */
#include <stdio.h>
#include <ctype.h>
#include <string.h>

int main()
{
    char str[100];
    int i;

    printf("Enter a string: ");
    fgets(str, sizeof(str), stdin);
    str[strcspn(str, "\n")] = '\0';

    for (i = 0; str[i] != '\0'; i++)
    {
        if (islower(str[i]))
            printf("%c is a lowercase letter\n", str[i]);
        else if (isupper(str[i]))
            printf("%c is an uppercase letter\n", str[i]);
        else if (isdigit(str[i]))
            printf("%c is a digit\n", str[i]);
        else
            printf("%c is a special character\n", str[i]);
    }

    return 0;
}
