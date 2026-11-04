#include <iostream>
using namespace std;

class Circle {
public:
    double radius;
    const double PI = 3.14;

    double calculateArea() {
        return PI * radius * radius;
    }

    double calculateCircumference() {
        return 2 * PI * radius;
    }
};

int main() {
    Circle c;

    c.radius = 5;

    cout << "Area: " << c.calculateArea() << endl;
    cout << "Circumference: " << c.calculateCircumference() << endl;

    return 0;
}