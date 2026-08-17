#include <stdio.h>
#include <stdlib.h>
#include <string.h>

struct Student {
    int roll_no;
    char name[50];
    float marks;
};

int main() {
    struct Student *s = (struct Student*)malloc(sizeof(struct Student));

    s->roll_no = 1;
    strcpy(s->name, "Amit");
    s->marks = 85.5;

    printf("Roll: %d\nName: %s\nMarks: %.1f\n",
           s->roll_no, s->name, s->marks);

    free(s);
    return 0;
}
