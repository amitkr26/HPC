#include <stdio.h>
#include <string.h>

struct Student {
    int roll;
    char name[50];
    float marks;
};

int main() {
    struct Student s1 = {1, "Amit", 85.5};

    FILE *fp = fopen("students.txt", "w");
    if(fp == NULL) { printf("Error\n"); return 1; }
    fprintf(fp, "%d %s %.1f", s1.roll, s1.name, s1.marks);
    fclose(fp);

    fp = fopen("students.txt", "r");
    if(fp == NULL) { printf("Error\n"); return 1; }
    struct Student s2;
    fscanf(fp, "%d %s %f", &s2.roll, s2.name, &s2.marks);
    printf("Read: %d %s %.1f\n", s2.roll, s2.name, s2.marks);
    fclose(fp);
    return 0;
}
