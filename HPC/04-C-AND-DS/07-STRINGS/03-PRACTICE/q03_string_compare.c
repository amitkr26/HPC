/* Q3. Input two strings and compare them using strcmp().
       Display whether they are equal or not. */
#include <stdio.h>
#include <string.h>

int main()
{
    char s1[100], s2[100];

    printf("Enter first string: ");
    fgets(s1, sizeof(s1), stdin);
    s1[strcspn(s1, "\n")] = '\0';

    printf("Enter second string: ");
    fgets(s2, sizeof(s2), stdin);
    s2[strcspn(s2, "\n")] = '\0';

    if (strcmp(s1, s2) == 0)
        printf("The strings are equal.\n");
    else
        printf("The strings are not equal.\n");

    return 0;
}
