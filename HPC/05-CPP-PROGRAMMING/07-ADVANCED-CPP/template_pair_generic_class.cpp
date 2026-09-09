#include <iostream>
#include <map>
#include <string>
using namespace std;
template<typename T1, typename T2>
class  Pair {
    public:
    T1 first;
    T2 second;
    Pair(T1 f, T2 s): first(f), second(s){}
    void print_pair(){
        cout << "First: " << first << ", Second: "<< second << endl;
    }
};


int main() {
   Pair<int, double> p1(10,20.5);
   p1.print_pair();
   Pair<std::string, std::string>p2("Hello", "World");
   p2.print_pair();

    return 0;
}