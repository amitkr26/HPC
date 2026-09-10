#include <iostream>

int add(int a, int b, int c=0);
inline int multiply(int a, int b){
    return a*b;
}
int factorial(int n){
    if(n<+1){
        return 1;
    }
    return n*factorial(n-1);
}

double add(double a, double b){
    return a+b;
}
void increment(int &val){
    val++;
}

void greet(std::string name, std::string greeting = "Hello"){
    std::cout<<greeting<<","<<name<<"!"<<std::endl;
}
int main() {
    int x=10;
    std::cout<<"add(1,2) with default arg. "<<add(1,2)<<std::endl;
    std::cout<<"add(1,2,3) "<<add(1,2,3)<<std::endl;
    std::cout<<"multiply(4,5) "<<multiply(4,5)<<std::endl;
    std::cout<<"factorial(5) "<<factorial(5)<<std::endl;
    std::cout<<"overloaded add(1.5,2.5) "<<add(1.5,2.5)<<std::endl;
    std::cout<<"before increament "<<x<<std::endl;
    increment(x);
    std::cout<<"after increament "<<x<<std::endl;
    greet("Alice");
    greet("bob", "hi");

    return 0;
}

int add(int a, int b, int c){
    return a+b+c;
}