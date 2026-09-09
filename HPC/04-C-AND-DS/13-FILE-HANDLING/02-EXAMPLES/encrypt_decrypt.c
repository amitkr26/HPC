#include <stdio.h>

void xorEncrypt(char *filename, char key) {
    FILE *fp = fopen(filename, "r+");
    if(fp == NULL) { printf("Error\n"); return; }
    char ch;
    long pos;
    while((ch = fgetc(fp)) != EOF) {
        pos = ftell(fp) - 1;
        fseek(fp, pos, SEEK_SET);
        fputc(ch ^ key, fp);
        fseek(fp, pos + 1, SEEK_SET);
    }
    fclose(fp);
}

int main() {
    FILE *fp = fopen("secret.txt", "w");
    fprintf(fp, "Hello World");
    fclose(fp);

    printf("Original: ");
    fp = fopen("secret.txt", "r");
    char ch;
    while((ch = fgetc(fp)) != EOF) printf("%c", ch);
    fclose(fp);
    printf("\n");

    xorEncrypt("secret.txt", 5);

    printf("Encrypted: ");
    fp = fopen("secret.txt", "r");
    while((ch = fgetc(fp)) != EOF) printf("%c", ch);
    fclose(fp);
    printf("\n");

    xorEncrypt("secret.txt", 5);
    printf("Decrypted: ");
    fp = fopen("secret.txt", "r");
    while((ch = fgetc(fp)) != EOF) printf("%c", ch);
    fclose(fp);
    printf("\n");
    return 0;
}
