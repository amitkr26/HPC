#include <iostream>
#include <string>
using namespace std;
class Book {
public:
    string title;
    string author;
    int pages;
    void displayinfo(){
        cout<<"Title:"<<title<<endl;
        cout<<"Author:"<<author<<endl;
        cout<<"Pages:"<<pages<<endl;
    }
};

int main()
{
    Book b1;
    b1.title = "The progragmatic Programmer";
    b1.author = "Hunt & thomas";
    b1.pages = 352;

    b1.displayinfo();

    return 0;
}