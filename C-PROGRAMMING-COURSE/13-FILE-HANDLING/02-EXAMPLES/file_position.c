#include <stdio.h>

int main() {
    FILE *fp = fopen("pos_test.txt", "w+");
    if(fp == NULL) { printf("Error\n"); return 1; }

    fprintf(fp, "ABCDEFGHIJ");
    printf("File written\n");

    rewind(fp);
    printf("Position after rewind: %ld\n", ftell(fp));

    fseek(fp, 5, SEEK_SET);
    printf("Position after seek(5): %ld\n", ftell(fp));

    char ch = fgetc(fp);
    printf("Character at pos 5: %c\n", ch);

    fclose(fp);
    return 0;
}
