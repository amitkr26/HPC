#include <iostream>
#include <string>
using namespace std;

int main() {
    string word;
    cout << "Enter a single word: ";
    cin >> word;

    string username = word;

    string fullTag = word + "_2026";
    cout << "Concatenated Strings: " << fullTag << endl;
    cout << "Length: " << fullTag.length() << " characters" << endl;

    string str1 = "admin_2026";
    if(str1 == fullTag){
        cout << "Access: Admin access granted" << endl;
    }
    else{
        cout << "Access: Regular user account created" << endl;

    }


    return 0;
}