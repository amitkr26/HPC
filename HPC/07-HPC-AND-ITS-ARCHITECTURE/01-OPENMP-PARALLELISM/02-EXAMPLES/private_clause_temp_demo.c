#include <stdio.h>
#include <omp.h>

int main()
{
    int temp = 10;

    #pragma omp parallel private(temp) num_threads(4)
    {
        int thread_id = omp_get_thread_num();

        if(thread_id == 4){
            temp = 50;
        }

        if(thread_id ==2){
            temp = 1000;
        }
    
        printf("thread id = %d has temp = %d\n", thread_id, temp);
    }

    printf("Outside: temp = %d", temp);

    return 0;
}