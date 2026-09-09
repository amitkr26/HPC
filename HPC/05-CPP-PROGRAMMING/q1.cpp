#include <iostream>
using namespace std;

class Calculator {
public:
    int compute(int a, int b) {
        return a + b;
    }

    float compute(float a, float b) {
        return a + b;
    }

    int compute(int a, int b, int c) {
        return a + b + c;
    }
};

int main() {
    Calculator calc;

    int intSum = calc.compute(10, 20);
    float floatSum = calc.compute(3.5f, 2.7f);
    int threeSum = calc.compute(5, 10, 15);

    cout << "Sum of two integers (10 + 20): " << intSum << endl;
    cout << "Sum of two floats (3.5 + 2.7): " << floatSum << endl;
    cout << "Sum of three integers (5 + 10 + 15): " << threeSum << endl;

    return 0;
}