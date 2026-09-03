#include <iostream>
#include <map>
using namespace std;

int main() {
    map<int, string> m;

    m.insert(pair<int, string>(1, "Alice"));
    m.insert(pair<int, string>(2, "Bob"));
    m.insert(pair<int, string>(3, "Charlie"));

    map<int, string>::iterator itr;

    cout << "Using iterator:" << endl;

    for (itr = m.begin(); itr != m.end(); ++itr) {
        cout << "ID: " << itr->first
             << ", Name: " << itr->second << endl;
    }

    cout << endl;

    cout << "Using range-based loop:" << endl;

    for (const auto& x : m) {
        cout << "ID: " << x.first
             << ", Name: " << x.second << endl;
    }

    return 0;
}