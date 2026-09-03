# Theory: Structures and Unions

## What is a Structure?
A structure is a user-defined data type that groups variables of different types under one name.

## Why Use Structures?
- Group related data together
- Create complex data types
- Pass multiple values to functions

## Declaring a Structure
```c
struct Student {
    int roll_no;
    char name[50];
    float marks;
};
```

## Creating Variables
```c
struct Student s1;
struct Student s2 = {1, "Amit", 85.5};
```

## Accessing Members (Dot Operator)
```c
s1.roll_no = 1;
strcpy(s1.name, "Amit");
s1.marks = 90.0;
```

## Arrays of Structures
```c
struct Student class[3];
class[0].roll_no = 1;
class[1].marks = 85.5;
```

## Structures as Function Arguments
```c
void printStudent(struct Student s) {
    printf("%s: %.1f\n", s.name, s.marks);
}
```

## Pointers to Structures
```c
struct Student s1 = {1, "Amit", 90.0};
struct Student *ptr = &s1;
printf("%s", ptr->name);     // arrow operator
printf("%s", (*ptr).name);   // same as above
```

## Nested Structures
```c
struct Date {
    int d, m, y;
};
struct Student {
    int roll_no;
    struct Date dob;
};
s1.dob.d = 15;
```

## typedef with Structures
```c
typedef struct {
    int x, y;
} Point;
Point p1 = {10, 20};  // no 'struct' keyword needed
```

## Unions
All members share the same memory location:
```c
union Data {
    int i;
    float f;
    char c;
};
union Data d;
d.i = 10;
// d.f and d.c now have garbage values
```
Size of union = size of largest member.
