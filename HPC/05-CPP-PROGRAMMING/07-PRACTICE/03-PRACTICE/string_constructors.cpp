#include <iostream>
#include <string>
using namespace std;

int main() {
    string s1 = "Hello";
    string s2("World");
    string s3(5, 'A');

    cout << s1 << s2 << s3 << endl;

    return 0;
}