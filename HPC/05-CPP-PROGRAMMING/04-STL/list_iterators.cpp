#include <iostream>
#include <list>
using namespace std;

int main() {
    list<int> v = {2, 4, 6, 8, 10};

    v.push_back(12);
    v.push_back(14);

    v.pop_back();

    cout << "List: ";
    for (int x : v) {
        cout << x << " ";
    }

    cout << endl;

    list<int>::iterator itr;

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