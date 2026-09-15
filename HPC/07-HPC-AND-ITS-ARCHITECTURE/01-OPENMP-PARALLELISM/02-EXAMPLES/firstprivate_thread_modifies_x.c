// #include <stdio.h>
// #include <omp.h>

// int main()
// {
//     int threshold = 100;

//     #pragma omp parallel firstprivate(threshold) num_threads(4)
//     {
//         int tid = omp_get_thread_num();

//         int result = threshold * (tid + 1);

//         for (int i = 0; i < 100000; i++);

//         printf("Thread %d: result = %d\n", tid, result);
//     }

//     printf("Outside: threshold = %d\n", threshold);

//     return 0;
// }



#include <stdio.h>
#include <omp.h>

int main()
{
    int x = 10;

    #pragma omp parallel firstprivate(x) num_threads(4)
    {
        int tid = omp_get_thread_num();

        if (tid == 3)
        {
            x = 50;
        }

        if (tid == 2)
        {
            x = 1000;
        }

        printf("Thread %d has x = %d\n", tid, x);
    }

    printf("Outside: x = %d\n", x);

    return 0;
}