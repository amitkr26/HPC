#include <iostream>
using namespace std;

class Test{
    public:
    int a;
    int *p;
    Test(int x){
        a = x;
        p = new int [a];
    }
    Test(const Test &t){
        a = t.a;
        p = new int[a];
        for(int i=0; i<a; i++){
            p[i] = t.p[i];
        }
    }
};

int main() {
    Test t(5);
    Test t1(t);

    cout << "t.a = " << t.a << endl;
    cout << "t.p = " << t.p << endl;
    cout << "t1.a = " << t.a << endl;
    cout << "t1.p = " << t1.p << endl;

    return 0;
}