#include <iostream>
#include <set>
using namespace std;

int main() {
    set<int> v = {2, 4, 6, 8, 10};

    v.insert(12);
    v.insert(14);

    v.erase();

    cout << "List: ";
    for (int x : v) {
        cout << x << " ";
    }

    cout << endl;

    set<int>::iterator itr;

    cout << "Using iterator: " << endl;

    for (itr = v.begin(); itr != v.end(); ++itr) {
        cout << *itr << " ";
    }

    cout << endl;

    cout << "Using range-based loop: " << endl;

    for (int x : v) {
        cout << x << " ";
    }

    cout << endl;

    return 0;
}