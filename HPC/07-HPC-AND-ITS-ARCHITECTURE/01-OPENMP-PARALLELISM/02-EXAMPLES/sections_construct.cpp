#include <iostream>
#include <omp.h>

int main() {
    #pragma omp parallel sections num_threads(2)
    {
        #pragma omp section
        std::cout << "Section 1 by thread " << omp_get_thread_num() << "\n";

        #pragma omp section
        std::cout << "Section 2 by thread " << omp_get_thread_num() << "\n";
    }
}