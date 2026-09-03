#include <iostream>
#include <cstdarg>
using namespace std;

void analyzeNumbers(int count, ...) {
    va_list args;
    va_start(args, count);

    int even = 0;
    int odd = 0;

    for (int i = 0; i < count; i++) {
        int value = va_arg(args, int);

        if (value % 2 == 0) {
            even++;
        }
        else {
            odd++;
        }
    }

    va_end(args);

    cout << "Even numbers: " << even << endl;
    cout << "Odd numbers: " << odd << endl;
}

int main() {

    analyzeNumbers(6, 10, 15, 20, 25, 30, 35);

    return 0;
}