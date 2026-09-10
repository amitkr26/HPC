#include <iostream>
#include <string>
using namespace std;

class Employee {
public:
    string name;
    int id;
    double salary;

    void displayDetails(){
        cout<<"Emaployee name: "<<name<<endl;
        cout<<"Emaployee id: "<<id<<endl;
        cout<<"Emaployee salary: "<<salary<<endl;
    }
};

int main() {
    Employee e;
    e.name = "Amit Kumar";
    e.id = 123;
    e.salary = 50000;

    e.displayDetails();

    return 0;
}