#include <iostream>
#include <string>
using namespace std;

class Complex{
    private:
    int real;
    int imag;

    public:
    Complex(int r, int i){
        real=r;
        imag = i;
    }

    Complex(const Complex &c){
        real=c.real;
        imag =c.imag;
    }

    void display(){
        cout<<real<<"+"<<imag<<"i"<<endl;
    }

};
int main() {
    Complex c1(3,4);
    Complex c2 = c1;

    c1.display();
    c2.display();

    return 0;
}