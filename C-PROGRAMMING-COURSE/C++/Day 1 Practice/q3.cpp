#include <iostream>
using namespace std;

class BankAccount {
private:
    int balance = 0;

public:
    void deposit(int amount) {
        balance = balance + amount;
        cout<<"Deposit of "<<amount<<" is successful"<<endl;
    }

    void withdraw(int amount) {
        if (amount > balance) {
            cout << "Invalid amount" << endl;
        }
        else {
            balance = balance - amount;
            cout<<amount<<" withdraw successful"<<endl;
        }
    }

    void checkBalance() {
        cout << "Balance: " << balance << endl;
    }
};

int main() {

    BankAccount a;

    a.deposit(1000);
    a.checkBalance();

    a.withdraw(300);
    a.checkBalance();

    a.withdraw(800);
    a.checkBalance();


    return 0;
}