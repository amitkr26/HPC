#include <stdio.h>

int main()
{
    FILE *fp = fopen("output.txt", "w");
    if(fp == NULL){
        printf("Cannot open file\n");
        return 1;
    }
    fputc('H', fp);
    fputc('e', fp);
    fputc('l', fp);
    fputc('l', fp);
    fputc('o', fp);
    fputc('\n', fp);

    fputs("Hello from fputs\n", fp);

    int age = 30;
    double score = 85.5;
    const char *name = "Amit";
    fprintf(fp, "Name: %s\nAge: %d\nScores: %.2f%", name, age, score);

    fclose(fp);
    printf("Successfully written\n");

    return 0;
}