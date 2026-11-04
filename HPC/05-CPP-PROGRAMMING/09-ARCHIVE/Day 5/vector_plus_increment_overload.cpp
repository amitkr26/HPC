#include <iostream>
using namespace std;

class Vector
{
private:
    int x,y;

public:
Vector(int x_val = 0, int y_val=0):x(x_val),y(y_val){}
Vector operator+(const Vector& other) const{
    return Vector(x + other.x, y + other.y);
}
Vector& operator++(){
    ++x;
    ++y;
    return *this;
}

friend std::ostream& operator<<(std::ostream& os, const Vector& v);
};

std::ostream &operator<<(std::ostream &os, const Vector& v)
{
    os << " Vector( " << v.x << " , " << v.y << ")";
    return os;
}
int main()
{
    Vector v1(1,2);
    Vector v2(3,4);
    Vector v3 = v1 + v2;
    cout << "v1: " << v1 << endl;
    cout << "v2: " << v2 << endl;
    cout << "v1 + v2 = " << v3 << endl;
    ++v1;
    cout << "After ++v1: " << v1 << endl;

    return 0;
}