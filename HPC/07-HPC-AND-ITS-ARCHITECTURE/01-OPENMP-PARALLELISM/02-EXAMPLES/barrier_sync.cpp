#include <iostream>
#include <omp.h>

int main() {
    int num_threads = 4;
    omp_set_num_threads(num_threads);

    #pragma omp parallel
    {
        int thread_id = omp_get_thread_num();
        
        // Print thread ID before the barrier
        std::cout << "Thread " << thread_id << " before the barrier.\n";
        
        // Wait for all threads to reach this point
        #pragma omp barrier
        
        // Print thread ID after the barrier
        std::cout << "Thread " << thread_id << " after the barrier.\n";
    }

    return 0;
}
