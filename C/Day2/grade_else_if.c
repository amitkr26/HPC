/*
 * Question: Take a student's marks as input and assign a grade using an
 *           else-if ladder:
 *           90-100 -> Grade A
 *           75-89  -> Grade B
 *           50-74  -> Grade C
 *           35-49  -> Grade D
 *           Below 35 -> Fail
 * Answer:   Input 92 -> "Grade A"
 *           Input 45 -> "Grade D"
 *           Input 20 -> "Fail"
 */
#include <stdio.h>

int main()
{
    int marks;

    printf("Enter the student's marks: ");
    scanf("%d", &marks);

    if(marks >= 90 && marks <= 100)
    {
        printf("Grade A\n");
    }
    else if(marks >= 75 && marks <= 89)
    {
        printf("Grade B\n");
    }
    else if(marks >= 50 && marks <= 74)
    {
        printf("Grade C\n");
    }
    else if(marks >= 35 && marks <= 49)
    {
        printf("Grade D\n");
    }
    else
    {
        printf("Fail\n");
    }

    return 0;
}
