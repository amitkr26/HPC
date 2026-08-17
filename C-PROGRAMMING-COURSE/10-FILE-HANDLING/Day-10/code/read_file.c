#include <stdio.h>

int main() {
    FILE *fp = fopen("output.txt", "r");
    if(fp == NULL) {
        printf("Cannot open file\n");
        return 1;
    }
    char ch;
    printf("File content:\n");
    while((ch = fgetc(fp)) != EOF)
        printf("%c", ch);
    fclose(fp);
    return 0;
}
