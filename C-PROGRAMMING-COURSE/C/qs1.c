#include <stdio.h>
#include <stdlib.h>

int main()
{
    int n, choice, marks_value;
    int *marks;

    printf("Enter number of students: ");
    scanf("%d", &n);

    marks = (int *)calloc(n, sizeof(int));

    if (marks == NULL)
    {
        printf("Memory allocation failed");
        return 1;
    }

    printf("Enter how many students' marks you want to fill: ");
    scanf("%d", &choice);

    for (int i = 0; i < choice; i++)
    {
        printf("Enter student number: ");
        int student;
        scanf("%d", &student);

        printf("Enter marks: ");
        scanf("%d", &marks[student - 1]);
    }

    printf("\nMarks array:\n");

    for (int i = 0; i < n; i++)
    {
        printf("Student %d = %d\n", i + 1, marks[i]);
    }

    free(marks);

    return 0;
}