#include <stdio.h>

int main() {
    FILE *fp = fopen("data.txt", "w");
    if(fp == NULL) { printf("Error\n"); return 1; }
    fprintf(fp, "Alice 90\n");
    fprintf(fp, "Bob 85\n");
    fprintf(fp, "Charlie 95\n");
    fclose(fp);

    fp = fopen("data.txt", "r");
    if(fp == NULL) { printf("Error\n"); return 1; }
    char name[50];
    int marks;
    while(fscanf(fp, "%s %d", name, &marks) == 2)
        printf("Name: %s, Marks: %d\n", name, marks);
    fclose(fp);
    return 0;
}
