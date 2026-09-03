#include <iostream>
#include <cstdarg>
using namespace std;

int main() {
    int *p = NULL;
    p = new int(10);
    int *p2 = new int[20];
    cout<<*p;
    delete p;
    delete[] p2;

    return 0;
}