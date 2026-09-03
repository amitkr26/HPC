/*
1. Fix the collision
B. Write a program with two namespaces India and USA, each having a function currency(). Call both functions.
*/

#include <iostream>

 namespace India{
    void currency(){
        std::cout<<"INR (India Rupees)."<<std::endl;
    }
 }
 namespace USA{
    void currency(){
        std::cout<<"USD (US Dollar)."<<std::endl;
    }
 }
int main() {
    India::currency();
    USA::currency();

    return 0;
}