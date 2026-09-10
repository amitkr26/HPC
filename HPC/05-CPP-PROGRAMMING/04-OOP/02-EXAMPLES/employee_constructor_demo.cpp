#include <iostream>
#include <string>
using namespace std;
 
class Employee{
    int id;
    double Salary;
    string name;
    public:

 Employee(){
        id = 0;
        Salary = 0;
        name = "Unknown";
    }

 Employee(int e, double s, string n){
        id = e;
        Salary = s;
        name = n;
    }

    void display(){
        cout << "Employee Name: "<<name << endl;
        cout << "Employee id: " <<id<< endl;
        cout << "Employee salary: "<<Salary << endl;

    }
};
 
int main()
{
    Employee e1;
    Employee e2(1, 20000, "Amit");
    e1.display();
    e2.display();
 
    return 0;
}