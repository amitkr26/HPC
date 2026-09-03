#include <iostream>
#include <string>
using namespace std;
class Car{
    public:
    string brand;
    Car(){
        brand = "Unknown";
        cout<<"Constructor ran for a car!"<<endl;
    }

};
int main() {
    cout<<"Before creating Car"<<endl;
    Car c1;
    cout<<"After creating Car"<<endl;

    return 0;
}