/* A. Create a nested namespace Company::HR containing an employee() function and access it from main(). */
#include <iostream>
namespace Company::HR {
    void employee(){
        std::cout<<"Employee."<<std::endl;
    }
}

int main() {
    Company::HR::employee();
    return 0;
}