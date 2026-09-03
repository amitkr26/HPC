#include <stdio.h>

struct Date {
    int d, m, y;
};

struct Employee {
    char name[50];
    float salary;
    struct Date joinDate;
};

int main() {
    struct Employee e = {"Mehul", 50000, {15, 8, 2024}};
    printf("Name: %s\n", e.name);
    printf("Salary: %.0f\n", e.salary);
    printf("Joined: %d/%d/%d\n", e.joinDate.d, e.joinDate.m, e.joinDate.y);
    return 0;
}
