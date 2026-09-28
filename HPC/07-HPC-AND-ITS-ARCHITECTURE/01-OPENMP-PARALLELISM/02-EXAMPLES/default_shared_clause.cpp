#include <iostream>
#include <omp.h>

int main() {
    int shared_variable = 5; // Variable shared among threads

    #pragma omp parallel num_threads(4) default(none) shared(shared_variable, std::cout)
    {
        std::cout << "Thread " << omp_get_thread_num() << ": Shared variable = " << shared_variable << "\n";
    }

    return (0);
}

//Assignment: same code without using 'shared'

