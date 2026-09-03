#include <iostream>
#include <memory>
using namespace std;
class Book{
    public:
    const int pages;
    int currentPage;
    Book(int numPages):pages(numPages),currentPage(1){}
    void displayPage()const{
        cout<< "current page: " <<currentPage << " of " << pages << endl;
    }
    void nextPage(){
        currentPage++;
    }
};

int main() {
    const Book classic(500);
    classic.displayPage();
    Book paperback(300);
    paperback.displayPage();
    paperback.nextPage();
    paperback.displayPage();

    return 0;
}