#include <stdio.h>

struct Date {
    int d, m, y;
};

struct Employee {
    int id;
    char name[50];
    struct Date joinDate;
};

int main() {
    struct Employee emp[3];
    int i, year;
    int found = 0;

    for (i = 0; i < 3; i++) {
        printf("Enter details of employee %d:\n", i + 1);
        printf("ID: ");
        scanf("%d", &emp[i].id);
        printf("Name: ");
        scanf("%s", emp[i].name);
        printf("Date of joining (dd mm yyyy): ");
        scanf("%d %d %d", &emp[i].joinDate.d, &emp[i].joinDate.m, &emp[i].joinDate.y);
    }

    printf("\nEnter year to check: ");
    scanf("%d", &year);

    printf("\nEmployees who joined before %d:\n", year);
    for (i = 0; i < 3; i++) {
        if (emp[i].joinDate.y < year) {
            printf("ID: %d, Name: %s, Joined: %d/%d/%d\n",
                   emp[i].id, emp[i].name,
                   emp[i].joinDate.d, emp[i].joinDate.m, emp[i].joinDate.y);
            found = 1;
        }
    }

    if (!found)
        printf("No employees found.\n");

    return 0;
}
