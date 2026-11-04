#include <iostream>
#include <omp.h>

int main() {
    int sum = 0;
    int i;

    // Using atomic construct
    #pragma omp parallel for
    for (i = 0; i < 10; i++) 
    {
        #pragma omp atomic	//NO block of code allowed, only ONE statement allowed with atomic
        sum += i; 		// Incrementing sum atomically
    }

    std::cout << "Sum using atomic construct: " << sum << std::endl;

    return 0;
}

//Assignment: try 'atomic' with block of code (expected: error/incorrect response)
