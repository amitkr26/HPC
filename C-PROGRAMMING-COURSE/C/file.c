#include <stdio.h>

int main()
{
    FILE *fptr;
    char data[] = "Hello, welcome to learn C programming";
    fptr = fopen("example.txt", "w");
    if(fptr == NULL){
        printf("Error: Could not open the file.\n");
        return 1;
    }
    fprintf(fptr, "%s", data);
    fclose(fptr);
    printf("Successfully wrote example.txt\n");
    return 0;


}