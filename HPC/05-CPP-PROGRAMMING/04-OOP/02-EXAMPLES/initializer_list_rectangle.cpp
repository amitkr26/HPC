#include <iostream>
using namespace std;

class Rectangle{
    private:
    int length;
    int breadth;
    public:
    Rectangle(int value1, int& ref1): length(value1), breadth(ref1){}
    void Area(){
        int area = length * breadth;
        cout << "Length:" << length << " Breadth :" << breadth <<endl;
        cout << "Area: " << area << endl;
    }
};

int main() {
    int target = 42;
    Rectangle ex(100, target);
    ex.Area();

    return 0;
}