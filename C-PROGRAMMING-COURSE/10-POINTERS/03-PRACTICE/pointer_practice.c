#include <stdio.h>

struct student{
    int roll;
    char name[50];
    float marks;
};
void printstr(struct student s);

int main(){
    struct student s1 = {23, "Mehul", 92};
    printstr(s1);
    
    return 0;
}

void printstr(struct student s){
    printf("Student Roll No is: %d\n", s.roll);
    printf("Student Name is: %s\n", s.name);
    printf("Student Marks are: %.2f\n", s.marks);
}