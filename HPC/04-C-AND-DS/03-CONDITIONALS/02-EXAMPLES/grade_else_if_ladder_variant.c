/*9. Write a C program that takes a student’s marks as input and assigns a grade using an
else-if ladder based on the following:
● 90–100 → Grade A
● 75–89 → Grade B
● 50–74 → Grade C
● 35–49 → Grade D
● Below 35 → Fail*/
#include<stdio.h>
int main()
{
    int marks;
    printf("Enter marks: ");
    scanf("%d", &marks);

    if(marks>=90)
    {
        printf("Grade is : A");
    }
    else if(marks>=75){
        printf("Grade is : B");

    }
    else if(marks>=50){
        printf("Grade is : C");

    }
    else if(marks>=35){
        printf("Grade is : D");

    }
    else{
        printf("Fail");
    }

    return 0;

}