#include <stdio.h>

int main() {
    FILE *src = fopen("source.txt", "r");
    FILE *dst = fopen("dest.txt", "w");
    if(src == NULL || dst == NULL) {
        printf("Error opening files\n");
        return 1;
    }
    char ch;
    while((ch = fgetc(src)) != EOF)
        fputc(ch, dst);
    fclose(src);
    fclose(dst);
    printf("File copied successfully\n");
    return 0;
}
