#include <iostream>
#include <string>
using namespace std;

int main()
{
    int age;
    string name;

    cout << "Enter your name: ";
    cin >> name;

    cout << "Enter your age: ";
    cin >> age;

    try
    {
        if (age < 0 || age > 90)
        {
            throw "Invalid age";
        }

        cout << "Age is valid: " << age << endl;
    }
    catch (const char* e)
    {
        cerr << "Error: " << e << endl;
    }

    cout << "End of program";

    return 0;
}