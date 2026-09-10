#include <iostream>
using namespace std;

int main() {
    int a;
    int b;
    cout << "Enter a: ";
    cin >> a;
    cout << "Enter b: ";
    cin >> b;
    auto larger = [](int a, int b) {return (a > b) ? a : b;};
    cout << "Larger: " << larger(a, b) << endl;

    return 0;
}