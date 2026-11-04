#include <iostream>
using namespace std;

class Number{
    private:
    const int value;
    int &ref;
    public:
    Number(int value1, int& ref1): value(value1), ref(ref1){}
    void display() const{
        cout << "Value:" << value << " Ref :" << ref <<endl;
    }

};

int main() {
    int target = 42;
    Number ex(100, target);
    ex.display();

    Number ex1(25, target);
    ex.display();

    return 0;
}