#include <iostream>
using namespace std;

class Date {
private:
    int day;
    int month;
    int year;

public:
    friend istream& operator>>(istream& input, Date& d);

    friend ostream& operator<<(ostream& output, const Date& d) {
        output << d.day << "/" << d.month << "/" << d.year << endl;
        return output;
    }
};

istream& operator>>(istream& input, Date& d) {
    cout << "Enter day, month and year: ";
    input >> d.day >> d.month >> d.year;
    return input;
}

int main() {
    Date d1;

    cin >> d1;
    cout << d1;

    return 0;
}