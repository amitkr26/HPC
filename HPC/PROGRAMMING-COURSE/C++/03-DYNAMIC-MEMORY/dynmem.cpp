#include <iostream>
#include <cstdarg>
using namespace std;

class Room{
    int length;
    int breadth;
    public:
    Room(int l, int b){
        length = l;
        breadth = b;
        cout << "length: " << length << endl;
        cout << "breadth: "<< breadth << endl;
    }
};

int main() {
    Room *p = new Room(10,20);
    delete p;

    return 0;
}