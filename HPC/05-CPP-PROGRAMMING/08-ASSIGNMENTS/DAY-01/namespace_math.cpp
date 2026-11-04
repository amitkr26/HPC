#include <iostream>
using namespace std;
namespace MyMath{
    double add(double a, double b){
        return a+b;
    }
}

namespace YourMath{
    double add(double a, double b){
        return a+b+1.0;
    }
}

int main()
{
    double result1 = MyMath::add(5.0, 3.0);
    double result2 = YourMath::add(5.0, 3.0);
    // std::cout<<"MyMath result: "<<result1<<std::endl;
    // std::cout<<"YourMath result: "<<result2<<std::endl;
    cout<<"MyMath result: "<<result1<< endl;
    cout<<"YourMath result: "<<result2<< endl;

    return 0;
}