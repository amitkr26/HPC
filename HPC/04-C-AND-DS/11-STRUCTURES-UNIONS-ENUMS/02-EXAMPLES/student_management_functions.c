#include <stdio.h>
#include <stdbool.h>

#define MAX 100

struct Student {
    int roll;
    char name[20];
    float marks;
};

void addStudent(struct Student *);
void displayStudent(struct Student);
void searchStudent(struct Student *, int);

int main() {
    struct Student s[MAX];
    int choice;
    int cnt = 0;

    do {
        printf("\n\nSelect the option:\n");
        printf("1) Add Student\n");
        printf("2) Display all Students\n");
        printf("3) Search\n");
        printf("4) Exit\n");
        printf("Enter choice: ");
        scanf("%d", &choice);

        switch (choice) {
            case 1:
                if (cnt < MAX) {
                    addStudent(&s[cnt]);
                    cnt++;
                } else {
                    printf("Student limit reached!\n");
                }
                break;

            case 2:
                if (cnt == 0) {
                    printf("No students available.\n");
                } else {
                    for (int i = 0; i < cnt; i++) {
                        displayStudent(s[i]);
                    }
                }
                break;

            case 3: {
                int roll;
                printf("Enter roll number to search: ");
                scanf("%d", &roll);
                searchStudent(s, roll);
                break;
            }

            case 4:
                printf("Exiting program...\n");
                break;

            default:
                printf("Invalid choice!\n");
        }

    } while (choice != 4);

    return 0;
}

void addStudent(struct Student *s) {
    printf("\nEnter Roll Number: ");
    scanf("%d", &s->roll);

    printf("Enter Name: ");
    scanf("%s", s->name);

    printf("Enter Marks: ");
    scanf("%f", &s->marks);

    printf("Student added successfully!\n");
}

void displayStudent(struct Student s) {
    printf("\n------ Student Details --------");
    printf("\nRoll Number: %d", s.roll);
    printf("\nName: %s", s.name);
    printf("\nMarks: %.2f\n", s.marks);
}

void searchStudent(struct Student *s, int roll) {
    for (int i = 0; i < MAX; i++) {
        if (s[i].roll == roll) {
            displayStudent(s[i]);
            return;
        }
    }

    printf("Student with roll number %d not found.\n", roll);
}
