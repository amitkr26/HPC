#include <iostream>
#include <string>
using namespace std;

class Shape
{
    public:
    double base, height;
    Shape(double b, double h)
    {
        base = b;
        height = h;
    }

    virtual double area()
    {
        cout << "Base Class area function called: " << endl;
        return 0;
    }
};

class Triangle : public Shape
{
    public:
    Triangle(double b, double h):Shape(b,h){}
    double area(){
        cout << "Derived Triangle Class area function called: " << endl;
        return 0.5 * base * height;
    }
    
};
class Rectangle : public Shape
{
    public:
    Rectangle(double b, double h):Shape(b,h){}
    double area(){
        cout << "Derived Rectangle Class area function called: " << endl;
        return base * height;
    }
    
};

int main()
{
    Shape *s1;
    Triangle t(10.0, 5.0);
    cout << "Area of Triangle: " << t.area() << endl;
    s1 = &t;
    cout << "Area of Triangle: " << s1->area() << endl;
    Rectangle r(10.0, 5.0);
    s1 = &r;
    cout << "Area of Rectangle: " << s1->area() << endl;


    return 0;
}