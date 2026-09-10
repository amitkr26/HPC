#include <iostream>
using namespace std;

class BankAccount {
private:
    int balance;
    int accountNumber;

public:

    BankAccount() {
        balance = 0;
    }


    BankAccount(int a, int initialBalance) {
        balance = initialBalance;
        accountNumber = a;
    }


    BankAccount(const BankAccount &c) {
        accountNumber = c.accountNumber;
        balance = c.balance;
    }

    void display() {
        cout << "Account Number: " << accountNumber << endl;
        cout << "Balance: " << balance << endl;
    }
};

int main() {
    BankAccount a1(123, 400);
    BankAccount a2 = a1;

    a1.display();
    a2.display();

    return 0;
}