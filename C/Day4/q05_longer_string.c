/* Q5. Input two strings. Compare their lengths using strlen()
       and display the longer string. */
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

    printf("Length of \"%s\" = %d\n", s1, (int)strlen(s1));
    printf("Length of \"%s\" = %d\n", s2, (int)strlen(s2));

    if (strlen(s1) > strlen(s2))
        printf("The longer string is: %s\n", s1);
    else if (strlen(s1) < strlen(s2))
        printf("The longer string is: %s\n", s2);
    else
        printf("Both strings have the same length.\n");

    return 0;
}
