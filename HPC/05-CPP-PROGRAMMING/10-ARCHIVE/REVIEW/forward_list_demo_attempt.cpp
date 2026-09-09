#include <iostream>
#include <map>
using namespace std;

int main() {
    set<int> v = {2, 4, 6, 8, 10};

    v.insert(12);
    v.insert(14);

    v.erase(10);

    cout << "Set: ";
    for (int x : v) {
        cout << x << " ";
    }

    cout << endl;

    set<int>::iterator itr;

    cout << "Using iterator: ";

    for (itr = v.begin(); itr != v.end(); ++itr) {
        cout << *itr << " ";
    }

    cout << endl;

    cout << "Using range-based loop: ";

    for (int x : v) {
        cout << x << " ";
    }

    cout << endl;

    return 0;
}