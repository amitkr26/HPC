#include <stdio.h>
#include <string.h>

struct Student {
    int roll_no;
    char name[50];
    float marks;
};

void sortByMarks(struct Student arr[], int n) {
    int i, j;
    struct Student temp;
    for(i = 0; i < n-1; i++) {
        for(j = 0; j < n-i-1; j++) {
            if(arr[j].marks < arr[j+1].marks) {
                temp = arr[j];
                arr[j] = arr[j+1];
                arr[j+1] = temp;
            }
        }
    }
}

int main() {
    struct Student class[3] = {
        {1, "Amit", 85.5},
        {2, "Rahul", 90.0},
        {3, "Priya", 78.5}
    };
    int i;
    sortByMarks(class, 3);
    printf("Sorted by marks (descending):\n");
    for(i = 0; i < 3; i++)
        printf("%d. %s: %.1f\n", class[i].roll_no, class[i].name, class[i].marks);
    return 0;
}
