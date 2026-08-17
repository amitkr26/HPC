#include <stdio.h>

int main()
{
    // FILE *fp = fopen("example.txt", "a");
    // if(fp == NULL){
    //     printf("Cannot open file\n");
    //     return 1;
    // }
    // fprintf(fp, "Appended line.\n");
    // printf("Successfully appended\n");
    // fclose(fp);
    rename("example.txt", "new.txt");

    return 0;
}