#include <iostream>
using namespace std;

class Box {
private:
    double length;
    double width;
    double height;

public:
    Box(double l, double w, double h) {
        length = l;
        width = w;
        height = h;
    }

    double volume() {
        return length * width * height;
    }

    bool operator>(Box other) {
        return volume() > other.volume();
    }

    Box operator+(Box other) {
        return Box(length + other.length,
                   width + other.width,
                   height + other.height);
    }

    friend ostream& operator<<(ostream& out, Box b) {
        out << "Box [" << b.length << " x " << b.width << " x " << b.height
            << "] Volume: " << b.volume();
        return out;
    }
};

int main() {
    Box b1(2.0, 3.0, 4.0);
    Box b2(1.0, 2.0, 3.0);

    if (b1 > b2) {
        cout << "Box 1 is larger than Box 2" << endl;
    } else {
        cout << "Box 2 is larger than or equal to Box 1" << endl;
    }

    Box b3 = b1 + b2;
    cout << "Result of addition: " << b3 << endl;

    return 0;
}