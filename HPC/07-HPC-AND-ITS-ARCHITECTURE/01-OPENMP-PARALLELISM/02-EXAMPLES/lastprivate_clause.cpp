#include<iostream>
#include<omp.h>

int main(void)
{
	int x = 44,i;
	
	#pragma omp parallel for num_threads(5) lastprivate(x)	
	//#pragma omp parallel for num_threads(5)
	for(i=0 ; i<10 ; i++)
	{
		x = i*2; 
		std::cout << "tid = " << omp_get_thread_num() << " , iteration = " << i << " , x = " << x << "\n";

	}
	 
	std::cout << "x=" << x << "\n";	//without lastprivate any random value will be updated by any thread

}
