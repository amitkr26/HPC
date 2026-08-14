#include <stdio.h>

struct student{
    int roll;
    char name[50];
    float marks;
};

int main(){
    struct student s1[3];
    int i;

    for(i=0; i<3; i++){
        printf("Enter Roll No, Name and Marks of Student: %d", i+1);
        scanf("%d %s %f", &s1[i].roll, s1[i].name, &s1[i].marks);
    }

    printf("\n---Student Details----\n");
    for(i=0; i<3; i++){
        printf("Student Roll No is: %d\n", s1[i].roll);
        printf("Student Name is: %s\n", s1[i].name);
        printf("Student Marks are: %.2f\n", s1[i].marks);
    }

    return 0;
}
