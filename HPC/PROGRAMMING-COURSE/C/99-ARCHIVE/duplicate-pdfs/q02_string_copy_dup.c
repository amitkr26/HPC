/* Q2. Input a string and copy it into another string using strcpy().
       Display both the original and copied strings. */
#include <stdio.h>
#include <string.h>

int main()
{
    char original[100], copied[100];

    printf("Enter a string: ");
    fgets(original, sizeof(original), stdin);
    original[strcspn(original, "\n")] = '\0';

    strcpy(copied, original);

    printf("Original string: %s\n", original);
    printf("Copied string  : %s\n", copied);

    return 0;
}
