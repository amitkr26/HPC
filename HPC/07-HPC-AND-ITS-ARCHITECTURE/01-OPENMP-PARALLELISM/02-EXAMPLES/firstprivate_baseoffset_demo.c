#include <stdio.h>
#include <omp.h>

int main()
{
    int baseoffset = 100;

    #pragma omp parallel firstprivate(baseoffset) num_threads(10)
    {
        int tid = omp_get_thread_num();

        int result = baseoffset + tid;

        printf("Thread %d: baseoffset = %d, result = %d\n",
               tid, baseoffset, result);
    }

    printf("Outside: baseoffset = %d\n", baseoffset);

    return 0;
}