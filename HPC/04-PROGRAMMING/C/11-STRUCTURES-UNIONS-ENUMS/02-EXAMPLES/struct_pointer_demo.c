#include <stdio.h>

struct Point {
    int x, y;
};

void printPoint(struct Point *p) {
    printf("Point: (%d, %d)\n", p->x, p->y);
}

int main() {
    struct Point p1 = {10, 20};
    struct Point *ptr = &p1;

    printf("Direct: (%d, %d)\n", p1.x, p1.y);
    printf("Pointer: (%d, %d)\n", ptr->x, ptr->y);
    printPoint(&p1);
    return 0;
}
