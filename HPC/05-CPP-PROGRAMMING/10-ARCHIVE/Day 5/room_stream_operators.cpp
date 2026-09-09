#include <iostream>
using namespace std;

class Room {
private:
    int length;
    int breadth;

public:
    friend istream& operator>>(istream &input, Room &r);
    friend ostream& operator<<(ostream &output, Room &r){
        output<<r.length<<"X"<<r.breadth<<endl;
        return output;
    }
};
  istream& operator>>(istream &input, Room &r){
        cout << "Enter leangth and breadth of Room: ";
        input >> r.length >> r.breadth;
        return input;
    }
int main() {
    Room r1;
    cin >> r1;
    cout << r1;

    return 0;
}