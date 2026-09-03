#include <stdio.h>

typedef struct {
    int x, y;
} Point;

typedef struct {
    Point center;
    int radius;
} Circle;

float distance(Point a, Point b) {
    int dx = a.x - b.x;
    int dy = a.y - b.y;
    return (dx*dx + dy*dy);
}

int main() {
    Point p1 = {10, 20};
    Point p2 = {40, 60};
    Circle c = {{0, 0}, 5};

    printf("P1: (%d,%d) P2: (%d,%d)\n", p1.x, p1.y, p2.x, p2.y);
    printf("Distance squared: %.0f\n", distance(p1, p2));
    printf("Circle center: (%d,%d) radius: %d\n", c.center.x, c.center.y, c.radius);
    return 0;
}
