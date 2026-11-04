#include <stdio.h>

struct student{
    int roll;
    char name[50];
    float marks;
};

struct student getStudent(int num);
void displayStudent(struct student s);

int main(){
    struct student s1[3];
    int i;

    for(i=0; i<3; i++){
        s1[i] = getStudent(i+1);
    }

    printf("\n---Student Details----\n");
    for(i=0; i<3; i++){
        displayStudent(s1[i]);
    }

    return 0;
}

struct student getStudent(int num){
    struct student s;
    printf("Enter Roll No, Name and Marks of Student: %d", num);
    scanf("%d %s %f", &s.roll, s.name, &s.marks);
    return s;
}

void displayStudent(struct student s){
    printf("Student Roll No is: %d\n", s.roll);
    printf("Student Name is: %s\n", s.name);
    printf("Student Marks are: %.2f\n", s.marks);
}
