#include <iostream>
using namespace std;

int main() {
    int number = 20;
    auto increase = [&number]() {number += 10;};
    increase();
    cout << "After increase: " << number << endl;
    
    return 0;
}