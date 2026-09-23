#include <iostream>
#include <omp.h>
#include <unistd.h>

using namespace std;

int main()
{
    omp_set_num_threads(4);

    #pragma omp parallel
    {
        int ID = omp_get_thread_num();

        cout << "Hello my ID is : " << ID << endl;

        sleep(10);
    }

    return 0;
}