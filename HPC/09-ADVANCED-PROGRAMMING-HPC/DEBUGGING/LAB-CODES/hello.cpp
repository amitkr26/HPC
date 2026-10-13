// Lab 1: basic GDB commands (break, run, next, print, set var)
#include <iostream>
using namespace std;

int main()
{
    int j = 3;
    int k = 7;

    j += k;        // j becomes 10
    k = j * 2;     // k becomes 20

    std::cout << "Hello everyone!!" << std::endl;
    return 0;
}
