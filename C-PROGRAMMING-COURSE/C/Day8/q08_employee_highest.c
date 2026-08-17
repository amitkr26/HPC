#include <stdio.h>

struct Employee {
    int id;
    char name[50];
    float salary;
};

int main() {
    struct Employee emp[5];
    int i, highest = 0;

    for (i = 0; i < 5; i++) {
        printf("Enter details of employee %d:\n", i + 1);
        printf("ID: ");
        scanf("%d", &emp[i].id);
        printf("Name: ");
        scanf("%s", emp[i].name);
        printf("Salary: ");
        scanf("%f", &emp[i].salary);
        if (emp[i].salary > emp[highest].salary)
            highest = i;
    }

    printf("\nEmployee with highest salary:\n");
    printf("ID: %d\n", emp[highest].id);
    printf("Name: %s\n", emp[highest].name);
    printf("Salary: %.2f\n", emp[highest].salary);

    return 0;
}
