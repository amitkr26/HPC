#include <iostream>
using namespace std;

class Rectangle {
public:
    int length;
    int width;

    int calculateArea(int length, int width) {
        int area = length * width;
        return area;
    }

    int calculatePerimeter(int length, int width) {
        int perimeter = 2 * (length + width);
        return perimeter;
    }
};

int main() {

    Rectangle r1;
    r1.length = 2;
    r1.width = 3;

    Rectangle r2;
    r2.length = 5;
    r2.width = 6;

    cout << "The area of Rectangle r1: "<< r1.calculateArea(r1.length, r1.width) << endl;
    cout << "The area of Rectangle r2: "<< r2.calculateArea(r2.length, r2.width) << endl;
    cout << "The perimeter of Rectangle r1: "<< r1.calculatePerimeter(r1.length, r1.width) << endl;
    cout << "The perimeter of Rectangle r2: "<< r2.calculatePerimeter(r2.length, r2.width) << endl;

    return 0;
}