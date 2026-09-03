/*Find the maximum of 3 numbers using deafault argument*/
#include <iostream>
using namespace std;

int maxi(int a, int b, int c = 0) {
    if (a >= b && a >= c) {
        return a;
    }
    else if (b >= a && b >= c) {
        return b;
    }
    else {
        return c;
    }
}

int main() {
    cout << maxi(40, 40, 40) << endl;
    cout << maxi(40, 40) << endl;

    return 0;
}