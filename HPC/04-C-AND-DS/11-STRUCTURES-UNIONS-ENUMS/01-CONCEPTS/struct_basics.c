#include <stdio.h>
#include <math.h>
struct student{
    int roll;
    char name[50];
    float marks;
};
int main(){
    struct student s1;
    printf("Enter Roll No: ");
    scanf("%d", &s1.roll);
    printf("Enter Name: ");
    scanf("%s", &s1.name);
    printf("Enter Marks: ");
    scanf("%f", &s1.marks);
    printf("\n---Student Details----\n");
    printf("Student Roll No is: %d\n Student Name is: %s\n Student Marks are: %.2f", s1.roll, s1.name,s1.marks);

    return 0;
}