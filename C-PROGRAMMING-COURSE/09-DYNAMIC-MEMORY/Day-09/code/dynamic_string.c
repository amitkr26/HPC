#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main() {
    char *str = (char*)malloc(100 * sizeof(char));

    printf("Enter a string: ");
    fgets(str, 100, stdin);
    str[strcspn(str, "\n")] = '\0';

    printf("You entered: %s\n", str);
    printf("Length: %lu\n", strlen(str));

    free(str);
    return 0;
}
