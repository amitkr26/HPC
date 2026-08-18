#include <stdio.h>

struct student{
    int roll;
    char name[50];
    float marks;
};
void printstr(struct student*);

int main(){
    struct student s1 = {23, "Mehul", 92};
    struct student *sp;
    sp=&s1;
    printstr(sp);
    
    return 0;
}

void printstr(struct student*p){
    printf("Student Roll No is: %d\n", p->roll);
    printf("Student Name is: %s\n", p->name);
    printf("Student Marks are: %.2f\n", p->marks);
}