#include <stdio.h>

int main() {
    FILE *fp = fopen("output.txt", "w");
    if(fp == NULL) {
        printf("Cannot open file\n");
        return 1;
    }
    fprintf(fp, "Name: Amit\n");
    fprintf(fp, "Age: 20\n");
    fprintf(fp, "Grade: A+\n");
    fclose(fp);
    printf("Written successfully\n");
    return 0;
}
