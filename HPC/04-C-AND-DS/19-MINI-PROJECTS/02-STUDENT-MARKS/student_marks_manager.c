/*
 * Student Marks Manager
 *
 * A menu-driven program that manages marks for up to 100 students, each with
 * 5 subjects. Uses only arrays, loops, conditions and switch - no structures
 * and no functions yet (those arrive in later lessons).
 *
 * Options:
 *   1. Add a student (roll number + 5 subject marks)
 *   2. Display all students (total, average, grade)
 *   3. Search a student by roll number
 *   4. Statistics (highest total, pass/fail count)
 *   5. Exit
 *
 * Built on: Day 3 (arrays, 2D arrays, linear search) + Day 2 (switch, loops).
 */
#include <stdio.h>

#define MAX_STUDENTS 100
#define SUBJECTS 5

int main()
{
    int roll[MAX_STUDENTS];        /* roll numbers */
    int marks[MAX_STUDENTS][SUBJECTS]; /* marks[student][subject] */
    int n = 0;                     /* how many students added */
    int choice, i, j, found;

    do
    {
        printf("\n======== STUDENT MARKS MANAGER ========\n");
        printf("1. Add Student\n");
        printf("2. Display All Students\n");
        printf("3. Search by Roll Number\n");
        printf("4. Statistics\n");
        printf("5. Exit\n");
        printf("Enter your choice: ");
        scanf("%d", &choice);

        switch (choice)
        {
            case 1:
                if (n >= MAX_STUDENTS)
                {
                    printf("Array is full. Cannot add more students.\n");
                    break;
                }
                printf("Enter roll number: ");
                scanf("%d", &roll[n]);

                /* Reject duplicate roll numbers. */
                found = 0;
                for (i = 0; i < n; i++)
                {
                    if (roll[i] == roll[n])
                    {
                        found = 1;
                        break;
                    }
                }
                if (found)
                {
                    printf("Roll number already exists. Not added.\n");
                    break;
                }

                printf("Enter marks for 5 subjects:\n");
                for (j = 0; j < SUBJECTS; j++)
                {
                    printf("  Subject %d: ", j + 1);
                    scanf("%d", &marks[n][j]);
                }
                n++;
                printf("Student added.\n");
                break;

            case 2:
                if (n == 0)
                {
                    printf("No students yet.\n");
                    break;
                }
                printf("\n%-8s", "Roll");
                for (j = 0; j < SUBJECTS; j++)
                {
                    printf(" S%d", j + 1);
                }
                printf("  Total   Avg  Grade\n");
                for (i = 0; i < n; i++)
                {
                    int total = 0;
                    for (j = 0; j < SUBJECTS; j++)
                    {
                        total = total + marks[i][j];
                    }
                    printf("%-8d", roll[i]);
                    for (j = 0; j < SUBJECTS; j++)
                    {
                        printf(" %2d", marks[i][j]);
                    }
                    printf("  %5d  %5.2f  ", total, total / (float)SUBJECTS);

                    /* Grade ladder from Day 2 (grade_else_if). */
                    if (total >= 450)
                        printf("A\n");
                    else if (total >= 375)
                        printf("B\n");
                    else if (total >= 250)
                        printf("C\n");
                    else if (total >= 175)
                        printf("D\n");
                    else
                        printf("Fail\n");
                }
                break;

            case 3:
                if (n == 0)
                {
                    printf("No students yet.\n");
                    break;
                }
                printf("Enter roll number to search: ");
                scanf("%d", &i);     /* reuse i as the search key */
                found = -1;
                for (j = 0; j < n; j++)
                {
                    if (roll[j] == i)
                    {
                        found = j;   /* j is the student's index */
                        break;
                    }
                }
                if (found == -1)
                {
                    printf("Roll number %d not found.\n", i);
                }
                else
                {
                    int total = 0;
                    printf("Marks of student %d:\n", roll[found]);
                    for (j = 0; j < SUBJECTS; j++)
                    {
                        printf("  Subject %d: %d\n", j + 1, marks[found][j]);
                        total = total + marks[found][j];
                    }
                    printf("Total = %d, Average = %.2f\n",
                           total, total / (float)SUBJECTS);
                }
                break;

            case 4:
                if (n == 0)
                {
                    printf("No students yet.\n");
                    break;
                }
                {
                    int highest = 0, passCount = 0;
                    for (i = 0; i < n; i++)
                    {
                        int total = 0;
                        for (j = 0; j < SUBJECTS; j++)
                        {
                            total = total + marks[i][j];
                        }
                        if (i == 0 || total > highest)
                        {
                            highest = total;
                        }
                        if (total >= 175)   /* "pass" uses the D grade floor */
                        {
                            passCount++;
                        }
                    }
                    printf("Students: %d\n", n);
                    printf("Pass: %d, Fail: %d\n", passCount, n - passCount);
                    printf("Highest total: %d\n", highest);
                }
                break;

            case 5:
                printf("Goodbye.\n");
                break;

            default:
                printf("Invalid choice. Try again.\n");
        }
    } while (choice != 5);

    return 0;
}
