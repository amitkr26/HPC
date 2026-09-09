#include <iostream>
#include <string>
using namespace std;

class Employee {
protected:
    string name;
    int empID;
    double basicSalary;

public:
    Employee(string n, int id, double salary) {
        name = n;
        empID = id;
        basicSalary = salary;
    }

    double calculateSalary() {
        return basicSalary;
    }

    string getName() {
        return name;
    }
};

class Manager : public Employee {
private:
    double bonus;

public:
    Manager(string n, int id, double salary, double b) : Employee(n, id, salary) {
        bonus = b;
    }

    double calculateSalary() {
        return basicSalary + bonus;
    }
};

class Trainee : public Employee {
private:
    double stipendDeduction;

public:
    Trainee(string n, int id, double salary, double deduction) : Employee(n, id, salary) {
        stipendDeduction = deduction;
    }

    double calculateSalary() {
        return basicSalary - stipendDeduction;
    }
};

int main() {
    Manager mgr("Amit Kumar", 101, 50000, 10000);
    Trainee trn("Rahul Sharma", 102, 15000, 2000);

    cout << "Employee: " << mgr.getName()
         << " | Salary: " << mgr.calculateSalary() << endl;

    cout << "Employee: " << trn.getName()
         << " | Salary: " << trn.calculateSalary() << endl;

    return 0;
}