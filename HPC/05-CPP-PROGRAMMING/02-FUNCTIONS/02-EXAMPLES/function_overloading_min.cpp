#include <iostream>
using namespace std;

int min(int a, int b) {
    if (a < b) {
        return a;
    }
    else {
        return b;
    }
}

float min(float a, float b) {
    if (a < b) {
        return a;
    }
    else {
        return b;
    }
}

int min(int a, int b, int c) {
    if (a <= b && a <= c) {
        return a;
    }
    else if (b <= a && b <= c) {
        return b;
    }
    else {
        return c;
    }
}

int main() {

    cout << min(10, 5) << endl;
    cout << min(12.5f, 3.4f) << endl;
    cout << min(10, 20, 3) << endl;

    return 0;
}