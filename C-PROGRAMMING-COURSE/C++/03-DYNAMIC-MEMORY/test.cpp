/*wap to create a class names student with rollNo and *marks (allocate dynamically)
The class should have a parametrized constructor to initialize rollNo and marks.
Display() to print marks and rollNo and memory address of marks
A setmarks()
*/
#include <iostream>
using namespace std;

class student{
    public:
    int rollNo;
    int marks;
    student(int r, int n){
       r = rollNo;
       m = marks;
    }
    student(const student &s){
        rollNo = s.rollNo;
        marks = s.marks;
    }
    void Display(){
        cout << "Marks :" << marks <<endl;
        cout << "Adress :" << &marks <<endl;
        cout << "Roll : " << rollNo <<endl;
    }
    void setmarks(int newmarks){
        marks = newmarks;
     }

};

int main() {
    student s(5, 50);
    student s2(s);
    s.Display();
    s2.Display();
    s.setmarks(8);
    s.Display();
    s2.Display();
    return 0;
}

