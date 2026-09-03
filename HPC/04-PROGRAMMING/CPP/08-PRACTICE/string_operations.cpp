#include <iostream>
#include <string>
using namespace std;

int main() {
    string original = "Apple";
    string copy = original;

    cout << "Original String: " << original << endl;
    cout << "Length: " << original.length() << " characters" << endl;

    string first = "Hello ";
    string second = "World!";
    string fullmessage = first + second;
    cout << "Concatenated Strings: " << fullmessage << endl;

    string str1 = "Cat";
    string str2 = "Dog";

    if(str1 == str2){
        cout << "Strings are equal." << endl;
    }
    else{
        cout << "\"" << str1 << "\n"" and \"" << str2 << "\" are NOT equal. \n";
    }

    return 0;
}