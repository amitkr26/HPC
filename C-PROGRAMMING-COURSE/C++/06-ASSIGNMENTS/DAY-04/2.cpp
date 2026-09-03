#include <iostream>
using namespace std;

int main() {
    int value = 50;
    auto f = [value]() {cout << "Value: " << value << endl;};
    f();

    return 0;
}