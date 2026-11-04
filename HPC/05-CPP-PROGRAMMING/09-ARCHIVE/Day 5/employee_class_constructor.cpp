#include <iostream>
#include <string>
using namespace std;

class Employee
{
    int empid;
    string name;
    double salary;

public:
    Employee(int eid, string n, double sal = 0.0)
        : empid(eid), name(n), salary(sal)
    {
    }

    void display()
    {
        cout << "Employee id: " << empid << endl;
        cout << "Employee name: " << name << endl;
        cout << "Employee salary: " << salary << endl;
    }

    void setName(string n)
    {
        name = n;
    }

    string getName()
    {
        return name;
    }

    void setSalary(double sal)
    {
        salary = sal;
    }

    double getSalary()
    {
        return salary;
    }
};

class ContractEmployee : public Employee
{
    int WorkHours;

public:
    ContractEmployee(int eid, string n, int wh)
        : Employee(eid, n)
    {
        WorkHours = wh;
        setSalary();
    }

    void setSalary()
    {
        Employee::setSalary(WorkHours * 100.0);
    }

    void display()
    {
        Employee::display();
        cout << "Working Hours: " << WorkHours << endl;
    }
};

int main()
{
    Employee e1(101, "Raj", 51000);
    e1.display();

    cout << endl;

    e1.setSalary(20000);
    e1.display();

    cout << endl;

    ContractEmployee ce2(102, "Riya", 160);
    ce2.display();

    return 0;
}