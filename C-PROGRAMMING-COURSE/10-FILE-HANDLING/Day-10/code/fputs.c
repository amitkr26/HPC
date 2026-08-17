#include <stdio.h>

int main()
{
    FILE *fp = fopen("output.txt", "w");
    if(fp == NULL){
        printf("Cannot open file\n");
        return 1;
    }

    fputs("Hello from fputs\nSecond line\n3rd line\n", fp);
    fputs("4th line\n", fp);
    fputs("5th line\n", fp);
    fputs("6th line\n", fp);

    // fprintf(fp, "");

    // int age = 30;
    // double score = 85.5;
    // const char *name = "Amit";
    // fprintf(fp, "Name: %s\nAge: %d\nScores: %.2f\n", name, age, score);

    fclose(fp);
    printf("Successfully written\n");

    // rename("Output.txt","renamed.txt");
    // remove("remove.txt");

    return 0;
}