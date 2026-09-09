/* Q8. Input two strings, concatenate them using strcat(), and display
       the concatenated string and the total number of characters using strlen(). */
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

    printf("Concatenated string: %s\n", s1);
    printf("Total number of characters = %d\n", (int)strlen(s1));

    return 0;
}
