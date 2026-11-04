#include <stdio.h>
#include <math.h>
struct employee{
    int id;
    char name[50];
    float salary;
};
int main(){
    struct employee e1;
    printf("Enter Employee id: ");
    scanf("%d", &e1.id);
    printf("Enter Name: ");
    scanf("%s", &e1.name);
    printf("Enter Salary: ");
    scanf("%f", &e1.salary);
    printf("\n---Employee Details----\n");
    printf("Employee id: %d\n Employee Name is: %s\n Employee Salary: %.2f", e1.id, e1.name,e1.salary);

    return 0;
}