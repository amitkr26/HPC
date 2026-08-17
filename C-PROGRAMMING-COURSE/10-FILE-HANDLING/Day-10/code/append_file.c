#include <stdio.h>

int main() {
    FILE *fp = fopen("output.txt", "a");
    if(fp == NULL) {
        printf("Cannot open file\n");
        return 1;
    }
    fprintf(fp, "Appended line 1\n");
    fprintf(fp, "Appended line 2\n");
    fclose(fp);
    printf("Appended successfully\n");
    return 0;
}
