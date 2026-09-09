#include <iostream>
using namespace std;

int main() {

    auto welcome = []() {
        cout << "Welcome to C++ Programming" << endl;
    };

    welcome();

    int value = 50;

    auto printValue = [value]() {
        cout << "Value: " << value << endl;
    };

    printValue();

    int number = 20;

    auto increase = [&number]() {
        number += 10;
    };

    increase();

    cout << "After increase: " << number << endl;

    auto square = [](int n) {
        return n * n;
    };

    cout << "Square: " << square(5) << endl;

    auto larger = [](int a, int b) {
        return (a > b) ? a : b;
    };

    cout << "Larger: " << larger(10, 25) << endl;

    auto evenOdd = [](int n) {
        if (n % 2 == 0)
            cout << n << " is Even" << endl;
        else
            cout << n << " is Odd" << endl;
    };

    evenOdd(7);

    auto checkSign = [](int n) {
        if (n > 0)
            cout << "Positive" << endl;
        else if (n < 0)
            cout << "Negative" << endl;
        else
            cout << "Zero" << endl;
    };

    checkSign(-5);

    return 0;
}