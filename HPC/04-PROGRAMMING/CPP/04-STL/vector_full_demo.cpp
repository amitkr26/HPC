#include <iostream>
#include <forward_list>
using namespace std;

int main() {
    forward_list<int> v = {2, 4, 6, 8, 10};

    v.push_front(12);
    v.push_front(14);

    v.pop_front();

    cout << "List: ";
    for (int x : v) {
        cout << x << " ";
    }

    cout << endl;

    forward_list<int>::iterator itr;

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