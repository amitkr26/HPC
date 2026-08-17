#include <stdio.h>

int main()
{
    FILE *fp = fopen("demo.txt", "w");
    if(fp == NULL){
        printf("Cannot open file\n");
        return 1;
    }

    fputc('H', fp);
    fputc('i', fp);
    fputc('\n', fp);

    fputs("Hello from fputs\n", fp);

    fprintf(fp, "Name: %s, Age: %d\n", "Amit", 20);

    fclose(fp);
    printf("Successfully written to demo.txt\n");

    return 0;
}
