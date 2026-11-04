#include <iostream>
using namespace std;

class Account {
    int accountNumber;
    double balance = 0.0;

public:

    Account(int accNo) : accountNumber(accNo) {}

    void deposit(double amount) {
        if (amount > 0) {
            balance = balance + amount;
        }
    }

    void withdraw(double amount) {
        if (amount <= balance) {
            balance = balance - amount;
        }
        else {
            cout << "Insufficient balance!" << endl;
        }
    }

    void displayBalance() {
        cout << "Account Number: " << accountNumber << endl;
        cout << "Available Balance: " << balance << endl;
    }

    double getBalance() {
        return balance;
    }

protected:
    void setBalance(double amount) {
        balance = amount;
    }
};


class SavingsAccount : public Account {

    double minimumBalance;

public:

    SavingsAccount(int accNo, double minBalance)
        : Account(accNo), minimumBalance(minBalance) {}

    void withdraw(double amount) {

        if (getBalance() - amount >= minimumBalance) {
            setBalance(getBalance() - amount);
        }
        else {
            cout << "Withdrawal denied! Minimum balance must be maintained."
                 << endl;
        }
    }
};


class CurrentAccount : public Account {

    double overdraftLimit;

public:

    CurrentAccount(int accNo, double limit)
        : Account(accNo), overdraftLimit(limit) {}

    void withdraw(double amount) {

        if (getBalance() - amount >= -overdraftLimit) {
            setBalance(getBalance() - amount);
        }
        else {
            cout << "Withdrawal denied! Overdraft limit exceeded."
                 << endl;
        }
    }
};


int main() {

    SavingsAccount savings(101, 1000);

    savings.deposit(5000);
    savings.withdraw(3000);
    savings.displayBalance();

    cout << endl;

    CurrentAccount current(102, 2000);

    current.deposit(5000);
    current.withdraw(6500);
    current.displayBalance();

    return 0;
}