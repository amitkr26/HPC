#include <iostream>
#include <string>
using namespace std;

class Login {
private:
    string password;

public:
    void setPassword(string pwd) {
        password = pwd;
    }

    bool checkPassword(string pwd) {
        return pwd == password;
    }
};

int main() {
    Login t1;

    t1.setPassword("27272");

    cout << "Wrong: "
         << t1.checkPassword("123") << endl;

    cout << "Correct: "
         << t1.checkPassword("27272") << endl;

    return 0;
}