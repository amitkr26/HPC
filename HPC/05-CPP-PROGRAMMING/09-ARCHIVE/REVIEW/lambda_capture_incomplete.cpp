#include <iostream>
#include <string>

using namespace std;
template

int main() {
    int a = 10;
    auto f = [&a] () { cout << a << endl;};
    f();
    a++;
    f();
}