#include <stdio.h>

int main()
{
    FILE *fptr;
    char data[] = "Hello, welcome to learn C programming";
    char ch;

    fptr = fopen("example.txt", "w");
    if(fptr == NULL){
        printf("Error: Could not open the file.\n");
        return 1;
    }
    fprintf(fptr, "%s", data);
    fclose(fptr);

    fptr = fopen("example.txt", "r");
    if(fptr == NULL){
        printf("Error: Could not open the file for reading.\n");
        return 1;
    }
    printf("Read: ");
    while((ch = fgetc(fptr)) != EOF){
        printf("%c", ch);
    }
    fclose(fptr);

    return 0;
}
