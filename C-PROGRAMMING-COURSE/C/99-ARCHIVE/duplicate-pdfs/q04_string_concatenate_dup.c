/* Q4. Input two strings and join them using strcat().
       Display the resulting string. */
#include <stdio.h>
#include <string.h>

int main()
{
    char s1[200], s2[100];

    printf("Enter first string: ");
    fgets(s1, sizeof(s1), stdin);
    s1[strcspn(s1, "\n")] = '\0';

    printf("Enter second string: ");
    fgets(s2, sizeof(s2), stdin);
    s2[strcspn(s2, "\n")] = '\0';

    strcat(s1, s2);

    printf("Resulting string: %s\n", s1);

    return 0;
}
