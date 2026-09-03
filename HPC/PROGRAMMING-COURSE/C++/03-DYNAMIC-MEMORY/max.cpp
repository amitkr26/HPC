#include <iostream>
#include<cstdarg>
using namespace std;

int maximum(int count, ...) {
    va_list args;
    va_start(args, count);
    int max = va_arg(args, int);

    for (int i =1; i<count; i++){
        int value = va_arg(args, int);
        if (value>max){
            max = value;
        }
    }
    va_end(args);
    return max;
}

int main() {
    int result = maximum(4, 15,8,25,10);
    cout << "The maximum is "<< result << endl;

    return 0;
}