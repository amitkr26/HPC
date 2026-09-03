#include <iostream>
#include <vector>
using namespace std;

int main() {
    vector<int>v={2,4,6,8,10};
    v.push_back(12);
    v.push_back(14);
    v.pop_back();
    for (int x: v){
        cout << x << "";
    }

    return 0;
}