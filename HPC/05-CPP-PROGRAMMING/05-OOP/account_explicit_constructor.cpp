#include <iostream>
#include <string>
using namespace std;

class Account
{
    int accNo;
    double balance;

public:
    Account()
    {
        accNo = 0;
        balance = 0;
    }

    Account(int e, double s, string n)
    {
        accNo = e;
        balance = s;
    }
    explicit Account(int){
        balance = 0;
    }

};

int main()
{
    Account a1(101, 5000);
    Account a2(102);



    return 0;
}