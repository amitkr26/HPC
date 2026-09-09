#include <stdio.h>

int main() {
    FILE *fp = fopen("output.txt", "r");
    if(fp == NULL) {
        printf("Cannot open file\n");
        return 1;
    }
    char buffer[256];
    int line = 1;
    while(fgets(buffer, sizeof(buffer), fp) != NULL) {
        printf("Line %d: %s", line, buffer);
        line++;
    }
    fclose(fp);
    return 0;
}
