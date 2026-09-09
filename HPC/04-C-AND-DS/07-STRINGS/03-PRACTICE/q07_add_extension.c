/* Q7. Input a filename and append the extension .txt using strcat(). */
#include <stdio.h>
#include <string.h>

int main()
{
    char filename[100];

    printf("Enter a filename: ");
    fgets(filename, sizeof(filename), stdin);
    filename[strcspn(filename, "\n")] = '\0';

    strcat(filename, ".txt");

    printf("File name with extension: %s\n", filename);

    return 0;
}
