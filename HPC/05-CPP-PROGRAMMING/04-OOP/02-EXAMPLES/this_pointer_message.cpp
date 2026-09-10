#include <iostream>
#include <string>
using namespace std;

class Message {
private:
    string from;
    string to;
    string body;

public:
    void setFrom(string from) {
        this->from = from;
    }

    string getFrom() const {
        return from;
    }
};

int main() {
    Message m;

    m.setFrom("Alice");

    cout << m.getFrom() << endl;

    return 0;
}