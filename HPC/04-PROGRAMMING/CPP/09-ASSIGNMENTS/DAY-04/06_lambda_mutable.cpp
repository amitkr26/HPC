#include <iostream>
using namespace std;

int main() {
    int n;
    cout << "Enter a number: ";
    cin >> n;
    auto evenOdd = [](int n) {
        if (n % 2 == 0)
            cout << n << " is Even" << endl;
        else
            cout << n << " is Odd" << endl;
    };

    evenOdd(n);

    return 0;
}