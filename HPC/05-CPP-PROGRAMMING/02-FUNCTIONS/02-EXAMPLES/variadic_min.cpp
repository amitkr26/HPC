#include <iostream>
#include<cstdarg>
using namespace std;

int minimum(int count, ...) {
    va_list args;
    va_start(args, count);
    int mini = va_arg(args, int);

    for (int i =1; i<count; i++){
        int value = va_arg(args, int);
        if (value<mini){
            mini = value;
        }
    }
    va_end(args);
    return mini;
}

int main() {
    int result = minimum(4, 15,8,25,10);
    cout << "The minimum is "<< result << endl;

    return 0;
}