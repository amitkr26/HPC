#include <stdio.h>
#define MAX 100

struct student{
    int roll;
    char name[50];
    float marks;
};

int main(){
    struct student s[MAX];
    int n = 0;
    int choice;
    int i;
    int roll;

    do{
        printf("\n---STUDENT MANAGEMENT----\n");
        printf("1. Add Student\n");
        printf("2. Display Students\n");
        printf("3. Search Student by Roll No\n");
        printf("4. Exit\n");
        printf("Enter your choice: ");
        scanf("%d", &choice);

        switch(choice){
        case 1:
            printf("Enter Roll No: ");
            scanf("%d", &s[n].roll);
            printf("Enter Name: ");
            scanf("%s", s[n].name);
            printf("Enter Marks: ");
            scanf("%f", &s[n].marks);
            n++;
            printf("Student added.\n");
            break;

        case 2:
            if(n == 0){
                printf("No students found.\n");
            }
            else{
                for(i=0; i<n; i++){
                    printf("Roll No: %d\n", s[i].roll);
                    printf("Name: %s\n", s[i].name);
                    printf("Marks: %.2f\n", s[i].marks);
                    printf("--------------\n");
                }
            }
            break;

        case 3:
            printf("Enter Roll No to search: ");
            scanf("%d", &roll);
            for(i=0; i<n; i++){
                if(s[i].roll == roll){
                    printf("Student Found!\n");
                    printf("Roll No: %d\n", s[i].roll);
                    printf("Name: %s\n", s[i].name);
                    printf("Marks: %.2f\n", s[i].marks);
                    break;
                }
            }
            if(i == n){
                printf("Student not found.\n");
            }
            break;

        case 4:
            printf("Exiting... Thank you!\n");
            break;

        default:
            printf("Invalid choice!\n");
        }
    }while(choice != 4);

    return 0;
}