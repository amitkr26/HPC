#include <iostream>
#include <string>
using namespace std;

class Complex{
    public:
    int real;
    int imag;

    explicit Complex(int r=0, int i=0){
        real=r;
        imag = i;
    }

    Complex(const Complex &c){
        real=c.real;
        imag =c.imag;
    }

};
void display(Complex c){
        cout<<c.real<<"+"<<c.imag<<"i"<<endl;
    }
int main() {
    Complex c1;

    display(Complex(10));

    return 0;
}