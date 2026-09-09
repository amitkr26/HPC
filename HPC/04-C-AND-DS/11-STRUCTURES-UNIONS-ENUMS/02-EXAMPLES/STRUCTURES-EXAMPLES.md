# Examples: Structures and Unions

## Example 1: Student Structure
```c
#include <stdio.h>
#include <string.h>
struct Student {
    int roll_no;
    char name[50];
    float marks;
};
int main() {
    struct Student s1 = {1, "Amit", 85.5};
    printf("Roll: %d\nName: %s\nMarks: %.1f\n",
           s1.roll_no, s1.name, s1.marks);
    return 0;
}
```

## Example 2: Array of Students
```c
#include <stdio.h>
struct Student {
    int roll_no;
    char name[50];
    float marks;
};
int main() {
    struct Student class[3] = {
        {1, "Amit", 85.5},
        {2, "Rahul", 90.0},
        {3, "Priya", 78.5}
    };
    int i;
    for(i = 0; i < 3; i++) {
        printf("%d. %s: %.1f\n",
            class[i].roll_no, class[i].name, class[i].marks);
    }
    return 0;
}
```

## Example 3: Structure with Pointer
```c
#include <stdio.h>
struct Student {
    int roll_no;
    char name[50];
    float marks;
};
void printStudent(struct Student *s) {
    printf("Roll: %d, Name: %s, Marks: %.1f\n",
           s->roll_no, s->name, s->marks);
}
int main() {
    struct Student s1 = {1, "Amit", 85.5};
    printStudent(&s1);
    return 0;
}
```

## Example 4: Nested Structure
```c
#include <stdio.h>
struct Date {
    int d, m, y;
};
struct Employee {
    char name[50];
    float salary;
    struct Date joinDate;
};
int main() {
    struct Employee e = {"Amit", 50000, {15, 8, 2024}};
    printf("%s joined on %d/%d/%d\n",
           e.name, e.joinDate.d, e.joinDate.m, e.joinDate.y);
    return 0;
}
```

## Example 5: Structure with Functions
```c
#include <stdio.h>
#include <string.h>
struct Student {
    int roll_no;
    char name[50];
    float marks;
};
struct Student createStudent(int r, char *n, float m) {
    struct Student s;
    s.roll_no = r;
    strcpy(s.name, n);
    s.marks = m;
    return s;
}
void updateMarks(struct Student *s, float newMarks) {
    s->marks = newMarks;
}
int main() {
    struct Student s1 = createStudent(1, "Amit", 80.0);
    printf("Before: %.1f\n", s1.marks);
    updateMarks(&s1, 95.0);
    printf("After: %.1f\n", s1.marks);
    return 0;
}
```
