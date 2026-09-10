#include <iostream>

class Point {
public:
    int x;
    int y;
};

int main()
{
    Point p1;
    p1.x = 10;
    p1.y = 20;

    Point p2;
    p2.x = 5;
    p2.y = 15;

    std::cout << "p1:(" << p1.x << ", " << p1.y << ")" << std::endl;
    std::cout << "p2:(" << p2.x << ", " << p2.y << ")" << std::endl;

    return 0;
}