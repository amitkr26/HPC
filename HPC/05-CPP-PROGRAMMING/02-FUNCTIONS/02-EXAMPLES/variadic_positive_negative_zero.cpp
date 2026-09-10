#include <iostream>
#include <cstdarg>
using namespace std;

void analyzeNumbers(int count, ...) {
    va_list args;
    va_start(args, count);

    int positive = 0;
    int negative = 0;
    int zero = 0;

    for (int i = 0; i < count; i++) {
        int value = va_arg(args, int);

        if (value>0) {
            positive++;
        }
        else if (value<0){
            negative++;
        }
        else if (value == 0){
            zero++;
        }
    }

    va_end(args);

    cout << "Positive: " << positive << endl;
    cout << "Negative: " << negative << endl;
    cout << "Zero: " << zero << endl;

}

int main() {

    analyzeNumbers(6, 10, 15, 20, 25, 30, 35);

    return 0;
}