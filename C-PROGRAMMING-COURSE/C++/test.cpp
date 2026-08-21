#include <iostream>
using namespace std;

class Ticket {
private:
    int seatNumber;
    float price;

public:

    Ticket() {
        seatNumber = 0;
        price = 0.0;
    }

    explicit Ticket(int s) {
        seatNumber = s;
        price = 200.00;
    }
    
    Ticket(int x, float y) {
        seatNumber = x;
        price = y;
    }

    Ticket(const Ticket &c) {
        seatNumber = c.seatNumber;
        price = c.price;
    }

    void display() {
        cout << "Seat Number: " << seatNumber << endl;
        cout << "Price: " << price << endl;
    }
};

int main() {

    Ticket t1;
    t1.display();

    Ticket t2(10);
    t2.display();

    Ticket t3(20, 800);
    t3.display();

    Ticket t4 = t3;
    t4.display();

    return 0;
}