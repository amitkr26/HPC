#include <stdio.h>

struct Student {
    int roll_no;
    char name[50];
    float marks[5];
};

int main() {
    struct Student s[5];
    int i, j, topper = 0;
    float total, maxTotal = 0;

    for (i = 0; i < 5; i++) {
        printf("Enter details of student %d:\n", i + 1);
        printf("Roll No: ");
        scanf("%d", &s[i].roll_no);
        printf("Name: ");
        scanf("%s", s[i].name);
        total = 0;
        for (j = 0; j < 5; j++) {
            printf("Marks in subject %d: ", j + 1);
            scanf("%f", &s[i].marks[j]);
            total = total + s[i].marks[j];
        }
        if (total > maxTotal) {
            maxTotal = total;
            topper = i;
        }
    }

    printf("\nStudent with highest total marks:\n");
    printf("Roll No: %d\n", s[topper].roll_no);
    printf("Name: %s\n", s[topper].name);
    printf("Total Marks: %.2f\n", maxTotal);

    return 0;
}
