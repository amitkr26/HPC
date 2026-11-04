#include <iostream>
#include <omp.h>

int main() {
    #pragma omp parallel num_threads(4)
    {
        #pragma omp single
        std::cout << "Single block by thread " << omp_get_thread_num() << "\n";
    }
}

// Assignment: master
