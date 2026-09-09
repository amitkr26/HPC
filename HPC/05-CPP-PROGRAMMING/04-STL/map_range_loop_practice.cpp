#include <iostream>
#include <map>
#include <string>
using namespace std;

int main() {
    map<int, string> m;

    m.insert(pair<int, string>(1, "Alice"));
    m.insert(pair<int, string>(2, "Bob"));
    m.insert(pair<int, string>(3, "Charlie"));

    cout << "All elements:" << endl;

    map<int, string>::iterator itr;

    for (itr = m.begin(); itr != m.end(); ++itr) {
        cout << itr->first << " => "
             << itr->second << endl;
    }

    auto itr1 = m.find(2);

    if (itr1 != m.end()) {
        cout << "Found: "
             << itr1->first << " => "
             << itr1->second << endl;
    }
    else {
        cout << "Not Found" << endl;
    }

    return 0;
}