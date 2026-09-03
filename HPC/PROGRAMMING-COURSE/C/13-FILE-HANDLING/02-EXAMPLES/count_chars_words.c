#include <stdio.h>
#include <ctype.h>

int main() {
    FILE *fp = fopen("output.txt", "r");
    if(fp == NULL) {
        printf("Cannot open file\n");
        return 1;
    }
    int chars = 0, words = 0, lines = 0;
    int inWord = 0;
    char ch;

    while((ch = fgetc(fp)) != EOF) {
        chars++;
        if(ch == '\n') lines++;
        if(isspace(ch))
            inWord = 0;
        else if(!inWord) {
            inWord = 1;
            words++;
        }
    }
    fclose(fp);
    printf("Characters: %d\n", chars);
    printf("Words: %d\n", words);
    printf("Lines: %d\n", lines);
    return 0;
}
