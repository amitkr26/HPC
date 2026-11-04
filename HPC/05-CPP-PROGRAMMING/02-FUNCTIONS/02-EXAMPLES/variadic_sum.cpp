#include <iostream>
#include<cstdarg>
using namespace std;

int sum(int count, ...) {
    va_list args;
    va_start(args, count);
    int sum = 0;
    for (int i =0; i<count; i++){
        sum += va_arg(args, int);
    }
    va_end(args);
    return sum;
}

int main() {
    int result = sum(4, 1,2,3,4);
    cout << "The sum is "<< result << endl;

    return 0;
}