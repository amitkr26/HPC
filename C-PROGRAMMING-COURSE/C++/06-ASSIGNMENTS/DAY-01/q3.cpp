#include <iostream>
#include <string>
using namespace std;

class Temperature  {
public:
    double celsius;

    double Fahrenheit(){
        return celsius * 9/5 + 32;
    }
};

int main() {
    Temperature t1;
    t1.celsius = 27;

    cout<<"The converted value:"<<t1.Fahrenheit()<<endl;

    return 0;
}