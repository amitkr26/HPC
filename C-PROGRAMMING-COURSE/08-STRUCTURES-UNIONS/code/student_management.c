/*
 * Student Management System
 *
 * A single-file C project that lets the user add, display, search, update,
 * delete and analyze student records. Data is stored in memory in an array
 * of structures.
 *
 * Features:
 *   1. Add a new student (unique roll number, name, marks of 5 subjects)
 *   2. Display all students with total, average and grade
 *   3. Search a student by roll number
 *   4. Update marks of a student
 *   5. Delete a student by roll number
 *   6. Show statistics (count, highest, lowest, pass/fail)
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_STUDENTS 100
#define SUBJECTS 5

typedef struct
{
    int roll;
    char name[50];
    float marks[SUBJECTS];
    float total;
    float average;
    char grade;
} Student;

Student students[MAX_STUDENTS];
int studentCount = 0;

void addStudent(void);
void displayAll(void);
void searchByRoll(void);
void updateMarks(void);
void deleteStudent(void);
void showStats(void);
void computeResult(Student *s);
char computeGrade(float average);
int findIndex(int roll);
void clearInputBuffer(void);

int main(void)
{
    int choice;

    do
    {
        printf("\n========== STUDENT MANAGEMENT SYSTEM ==========\n");
        printf("1. Add Student\n");
        printf("2. Display All Students\n");
        printf("3. Search Student by Roll Number\n");
        printf("4. Update Student Marks\n");
        printf("5. Delete Student\n");
        printf("6. Statistics\n");
        printf("7. Exit\n");
        printf("Enter your choice: ");
        scanf("%d", &choice);
        clearInputBuffer();

        switch (choice)
        {
            case 1: addStudent();  break;
            case 2: displayAll();  break;
            case 3: searchByRoll(); break;
            case 4: updateMarks(); break;
            case 5: deleteStudent(); break;
            case 6: showStats();   break;
            case 7: printf("Exiting program...\n"); break;
            default: printf("Invalid choice. Please try again.\n");
        }
    } while (choice != 7);

    return 0;
}

/* Adds a new student after validating roll number and marks. */
void addStudent(void)
{
    int i;

    if (studentCount >= MAX_STUDENTS)
    {
        printf("Database is full! Cannot add more students.\n");
        return;
    }

    printf("\n--- Add Student ---\n");
    printf("Enter roll number: ");
    scanf("%d", &students[studentCount].roll);
    clearInputBuffer();

    if (findIndex(students[studentCount].roll) != -1)
    {
        printf("A student with roll number %d already exists.\n",
               students[studentCount].roll);
        return;
    }

    printf("Enter name: ");
    fgets(students[studentCount].name, sizeof(students[studentCount].name), stdin);
    students[studentCount].name[strcspn(students[studentCount].name, "\n")] = '\0';

    printf("Enter marks of %d subjects (0 to 100):\n", SUBJECTS);
    for (i = 0; i < SUBJECTS; i++)
    {
        do
        {
            printf("  Subject %d: ", i + 1);
            scanf("%f", &students[studentCount].marks[i]);
            if (students[studentCount].marks[i] < 0 || students[studentCount].marks[i] > 100)
            {
                printf("  Marks must be between 0 and 100. Try again.\n");
            }
        } while (students[studentCount].marks[i] < 0 || students[studentCount].marks[i] > 100);
    }
    clearInputBuffer();

    computeResult(&students[studentCount]);
    studentCount++;

    printf("Student added successfully!\n");
}

/* Prints all students in a formatted table. */
void displayAll(void)
{
    int i, j;

    if (studentCount == 0)
    {
        printf("\nNo students in the database.\n");
        return;
    }

    printf("\n--- All Students ---\n");
    printf("%-6s %-20s %-30s %-8s %-8s %-6s\n",
           "Roll", "Name", "Marks", "Total", "Avg", "Grade");
    printf("---------------------------------------------------------------"
           "-------------\n");

    for (i = 0; i < studentCount; i++)
    {
        printf("%-6d %-20s ", students[i].roll, students[i].name);

        for (j = 0; j < SUBJECTS; j++)
        {
            printf("%.0f ", students[i].marks[j]);
        }

        printf("%-8.2f %-8.2f %-6c\n",
               students[i].total, students[i].average, students[i].grade);
    }
}

/* Searches for a student by roll number and prints the details. */
void searchByRoll(void)
{
    int roll, index;

    printf("\n--- Search Student ---\n");
    printf("Enter roll number to search: ");
    scanf("%d", &roll);
    clearInputBuffer();

    index = findIndex(roll);

    if (index == -1)
    {
        printf("Student with roll number %d not found.\n", roll);
        return;
    }

    printf("Roll    : %d\n", students[index].roll);
    printf("Name    : %s\n", students[index].name);
    printf("Marks   : ");
    for (int i = 0; i < SUBJECTS; i++)
    {
        printf("%.2f ", students[index].marks[i]);
    }
    printf("\n");
    printf("Total   : %.2f\n", students[index].total);
    printf("Average : %.2f\n", students[index].average);
    printf("Grade   : %c\n", students[index].grade);
}

/* Updates the marks of an existing student and recomputes the result. */
void updateMarks(void)
{
    int roll, index, i;

    printf("\n--- Update Student Marks ---\n");
    printf("Enter roll number: ");
    scanf("%d", &roll);
    clearInputBuffer();

    index = findIndex(roll);

    if (index == -1)
    {
        printf("Student with roll number %d not found.\n", roll);
        return;
    }

    printf("Enter new marks of %d subjects (0 to 100) for %s:\n",
           SUBJECTS, students[index].name);

    for (i = 0; i < SUBJECTS; i++)
    {
        do
        {
            printf("  Subject %d: ", i + 1);
            scanf("%f", &students[index].marks[i]);
            if (students[index].marks[i] < 0 || students[index].marks[i] > 100)
            {
                printf("  Marks must be between 0 and 100. Try again.\n");
            }
        } while (students[index].marks[i] < 0 || students[index].marks[i] > 100);
    }
    clearInputBuffer();

    computeResult(&students[index]);
    printf("Marks updated successfully!\n");
}

/* Deletes a student by roll number and shifts the remaining records left. */
void deleteStudent(void)
{
    int roll, index, i;

    printf("\n--- Delete Student ---\n");
    printf("Enter roll number to delete: ");
    scanf("%d", &roll);
    clearInputBuffer();

    index = findIndex(roll);

    if (index == -1)
    {
        printf("Student with roll number %d not found.\n", roll);
        return;
    }

    for (i = index; i < studentCount - 1; i++)
    {
        students[i] = students[i + 1];
    }

    studentCount--;
    printf("Student with roll number %d deleted successfully.\n", roll);
}

/* Shows aggregate statistics about all students. */
void showStats(void)
{
    int i, j;
    int passCount = 0, failCount = 0;
    int highestIndex = 0, lowestIndex = 0;
    float totalOfAll = 0.0;

    if (studentCount == 0)
    {
        printf("\nNo students in the database.\n");
        return;
    }

    for (i = 0; i < studentCount; i++)
    {
        totalOfAll += students[i].total;

        if (students[i].average >= 35)
        {
            passCount++;
        }
        else
        {
            failCount++;
        }

        if (students[i].total > students[highestIndex].total)
        {
            highestIndex = i;
        }

        if (students[i].total < students[lowestIndex].total)
        {
            lowestIndex = i;
        }
    }

    printf("\n--- Statistics ---\n");
    printf("Number of students : %d\n", studentCount);
    printf("Total marks of all : %.2f\n", totalOfAll);
    printf("Average per student: %.2f\n", totalOfAll / studentCount);
    printf("Passed students    : %d\n", passCount);
    printf("Failed students    : %d\n", failCount);
    printf("Highest scorer     : %s (Roll %d, Total %.2f)\n",
           students[highestIndex].name, students[highestIndex].roll,
           students[highestIndex].total);
    printf("Lowest scorer      : %s (Roll %d, Total %.2f)\n",
           students[lowestIndex].name, students[lowestIndex].roll,
           students[lowestIndex].total);

    for (j = 0; j < SUBJECTS; j++)
    {
        float subjectTotal = 0.0;
        float subjectMax = students[0].marks[j];
        float subjectMin = students[0].marks[j];

        for (i = 0; i < studentCount; i++)
        {
            subjectTotal += students[i].marks[j];
            if (students[i].marks[j] > subjectMax)
            {
                subjectMax = students[i].marks[j];
            }
            if (students[i].marks[j] < subjectMin)
            {
                subjectMin = students[i].marks[j];
            }
        }

        printf("Subject %d: class average = %.2f, highest = %.2f, lowest = %.2f\n",
               j + 1, subjectTotal / studentCount, subjectMax, subjectMin);
    }
}

/* Computes total, average and grade for a single student. */
void computeResult(Student *s)
{
    int i;

    s->total = 0.0;

    for (i = 0; i < SUBJECTS; i++)
    {
        s->total += s->marks[i];
    }

    s->average = s->total / SUBJECTS;
    s->grade = computeGrade(s->average);
}

/* Grade boundaries: 90+ = A, 75+ = B, 50+ = C, 35+ = D, below 35 = F. */
char computeGrade(float average)
{
    if (average >= 90)
    {
        return 'A';
    }
    else if (average >= 75)
    {
        return 'B';
    }
    else if (average >= 50)
    {
        return 'C';
    }
    else if (average >= 35)
    {
        return 'D';
    }
    else
    {
        return 'F';
    }
}

/* Returns the index of the student with the given roll number, or -1. */
int findIndex(int roll)
{
    int i;

    for (i = 0; i < studentCount; i++)
    {
        if (students[i].roll == roll)
        {
            return i;
        }
    }

    return -1;
}

/* Discards any leftover characters in the input buffer. */
void clearInputBuffer(void)
{
    int c;

    while ((c = getchar()) != '\n' && c != EOF)
    {
    }
}
