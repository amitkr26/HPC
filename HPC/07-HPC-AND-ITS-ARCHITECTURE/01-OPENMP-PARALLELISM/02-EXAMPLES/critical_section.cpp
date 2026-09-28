#include <iostream>
#include <omp.h>

int main() {
    int sum = 0;
    int i;

    #pragma omp parallel for num_threads(10)
    for (i = 0; i < 10; i++) 
    {
        #pragma omp critical	//multiple statement (block of code allowed)
        {
            sum += i; // Incrementing sum safely within the critical section
	    //sum = sum + 5;
        }
    }

    std::cout << "Sum using critical construct: " << sum << std::endl;

    return (0);
}
