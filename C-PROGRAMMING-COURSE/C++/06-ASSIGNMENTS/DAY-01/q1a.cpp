/*
1. Fix the collision
A. Two functions both named area() are needed — one for a Circle and one for a Square. Write the code so both can exist in the same file without a redefinition error, using namespaces and the scope resolution operator.
*/

#include <iostream>

 namespace Circle{
    float area(float r){
        float PI = 3.14;
        float x = PI*r*r;
        std::cout<<"Area of Circle is: "<<x<<std::endl;
        return x;
    }
 }
 namespace Square{
    float area(float a){
        float y = a*a;
        std::cout<<"Area of Sqaure is: "<<y<<std::endl;
        return y;
    }
 }
int main() {
    Circle::area(5);
    Square::area(5);

    return 0;
}