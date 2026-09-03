#include <iostream>
using namespace std;

class Example{
    private:
    const int max_value;
    int &original_ref;
    public:
    Example(int max, int& external_var): max_value(max), original_ref(external_var){}
    void display() const{
        cout << "Const Max:" << max_value << "Ref Value:" << original_ref <<endl;
    }

};

int main() {
    int target = 42;
    Example ex(100, target);
    ex.display();

    return 0;
}