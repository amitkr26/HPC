#include <iostream>
#include <string>
using namespace std;

class Employee
{
    int id;
    double Salary;
    string name;

public:
    Employee()
    {
        id = 0;
        Salary = 0;
        name = "Unknown";
    }

    Employee(int e, double s, string n)
    {
        id = e;
        Salary = s;
        name = n;
    }
    Employee(const Employee &other)
    {
        id = other.id;
        Salary = other.Salary;
        name = other.name;

        cout << "Copy constructor called" << endl;
    }

    void display()
    {
        cout << "Employee Name: " << name << endl;
        cout << "Employee id: " << id << endl;
        cout << "Employee salary: " << Salary << endl;
    }
};

int main()
{
    Employee e1(1, 20000, "Amit");
    Employee e2 = e1;

    cout << "Employee 1:" << endl;
    e1.display();

    cout << "\nEmployee 2:" << endl;
    e2.display();

    return 0;
}