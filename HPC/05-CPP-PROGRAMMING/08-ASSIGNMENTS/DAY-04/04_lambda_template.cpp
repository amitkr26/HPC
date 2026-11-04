#include <iostream>
using namespace std;
int main() {
    int n;
    cout << "Enter a number: ";
    cin >> n;
    auto square = [](int n) {return n * n;};
    cout << "Square: " << square(n) << endl;
    
    return 0;
}