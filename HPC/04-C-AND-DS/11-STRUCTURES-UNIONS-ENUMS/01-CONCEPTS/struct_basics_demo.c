#include <stdio.h>
#include <string.h>

struct Student {
    int roll_no;
    char name[50];
    float marks;
};

int main() {
    struct Student s1 = {1, "Mehul", 85.5};
    struct Student s2;

    s2.roll_no = 2;
    strcpy(s2.name, "Rahul");
    s2.marks = 90.0;

    printf("Student 1: %d, %s, %.1f\n", s1.roll_no, s1.name, s1.marks);
    printf("Student 2: %d, %s, %.1f\n", s2.roll_no, s2.name, s2.marks);
    return 0;
}
