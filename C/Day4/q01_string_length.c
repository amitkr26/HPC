/* Q1. Read a string from the user and display its length using strlen(). */
#include <stdio.h>
#include <string.h>

int main()
{
    char str[100];

    printf("Enter a string: ");
    fgets(str, sizeof(str), stdin);
    str[strcspn(str, "\n")] = '\0';

    printf("The string is: %s\n", str);
    printf("Length of the string = %d\n", (int)strlen(str));

    return 0;
}
