#include <iostream>
#include <map>
using namespace std;

int main() {
    map<int, string> m;

    m.insert(pair<int, string>(1, "Alice"));
    m.insert(pair<int, string>(2, "Bob"));
    m.insert(pair<int, string>(3, "Charlie"));

    map<int, string>::iterator itr;

    for (itr = m.begin(); itr != m.end(); ++itr) {
        cout << *itr << " ";
    }

    cout << endl;

    cout << "Using range-based loop: ";

    for (int x : m) {
        cout << x << " ";
    }

    cout << endl;

    return 0;
}