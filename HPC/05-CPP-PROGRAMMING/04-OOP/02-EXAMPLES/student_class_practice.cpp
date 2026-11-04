#include <iostream>
#include <iomanip>
#include <sstream>
using namespace std;
 
class Student{
    int rollnumber;
    int marks;
    string name;

    Student(){
        rollnumber = 0;
        marks = 0;
        name = "Unknown"
    }

    Student(int r, int m, string n){
        r = rollnumber;
        m = marks;
        n = name;
    }
}
 
int main()
{
 
    return 0;
}