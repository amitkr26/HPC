#include <iostream>
using namespace std;

int main()
{
    try{
        int *arr[100000000];
    }
    catch(exception &e){
        cerr<<"Standard exception: " << e.what() <<endl;
    }
    cout<<"End of program";

    return 0;
}