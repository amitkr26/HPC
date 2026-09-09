#include <stdio.h>

int main()
{
    int marks[5][3][5];

    int i, j, k;
    int department;
    int total;
    float average;

    for (i = 0; i < 5; i++)
    {
        printf("\n=== Entering marks for Department %d ===\n", i + 1);

        for (j = 0; j < 3; j++)
        {
            printf("\nStudent %d:\n", j + 1);

            for (k = 0; k < 5; k++)
            {
                printf("Subject %d marks: ", k + 1);
                scanf("%d", &marks[i][j][k]);
            }
        }
    }

    printf("\nEnter department number to display results (1-5): ");
    scanf("%d", &department);

    if (department < 1 || department > 5)
    {
        printf("Invalid department number!\n");
        return 1;
    }

    department = department - 1;

    printf("\n===== Department %d Results =====\n", department + 1);

    for (j = 0; j < 3; j++)
    {
        total = 0;

        for (k = 0; k < 5; k++)
        {
            total = total + marks[department][j][k];
        }

        average = total / 5.0;

        printf("Student %d -> Total: %d, Average: %.2f\n",
               j + 1, total, average);
    }

    return 0;
}