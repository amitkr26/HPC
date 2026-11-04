# Examples: File Handling

## Example 1: Write to File
```c
#include <stdio.h>
int main() {
    FILE *fp = fopen("output.txt", "w");
    if(fp == NULL) {
        printf("Cannot open file\n");
        return 1;
    }
    fprintf(fp, "Name: Amit\n");
    fprintf(fp, "Age: 20\n");
    fclose(fp);
    printf("Written successfully\n");
    return 0;
}
```

## Example 2: Read from File
```c
#include <stdio.h>
int main() {
    FILE *fp = fopen("output.txt", "r");
    if(fp == NULL) {
        printf("Cannot open file\n");
        return 1;
    }
    char ch;
    while((ch = fgetc(fp)) != EOF)
        printf("%c", ch);
    fclose(fp);
    return 0;
}
```

## Example 3: Append to File
```c
#include <stdio.h>
int main() {
    FILE *fp = fopen("output.txt", "a");
    if(fp == NULL) {
        printf("Cannot open file\n");
        return 1;
    }
    fprintf(fp, "Appended line\n");
    fclose(fp);
    printf("Appended successfully\n");
    return 0;
}
```

## Example 4: Read/Write (r+ mode)
```c
#include <stdio.h>
int main() {
    FILE *fp = fopen("output.txt", "r+");
    if(fp == NULL) {
        printf("Cannot open file\n");
        return 1;
    }
    char ch;
    while((ch = fgetc(fp)) != EOF)
        printf("%c", ch);
    fseek(fp, 0, SEEK_END);
    fprintf(fp, "New line added\n");
    fclose(fp);
    return 0;
}
```

## Example 5: File with Struct
```c
#include <stdio.h>
#include <string.h>
struct Student {
    int roll;
    char name[50];
    float marks;
};
int main() {
    struct Student s1 = {1, "Amit", 85.5};
    FILE *fp = fopen("students.dat", "w");
    if(fp == NULL) return 1;
    fprintf(fp, "%d %s %.1f", s1.roll, s1.name, s1.marks);
    fclose(fp);
    fp = fopen("students.dat", "r");
    struct Student s2;
    fscanf(fp, "%d %s %f", &s2.roll, s2.name, &s2.marks);
    printf("Read: %d %s %.1f\n", s2.roll, s2.name, s2.marks);
    fclose(fp);
    return 0;
}
```
