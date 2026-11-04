#include<iostream>

#include<omp.h>

int x  , tid ;

#pragma omp threadprivate(x , tid)	//threadprivate can be applied to global variables only

int main(void)
{
	int i ;
	omp_set_num_threads(5);

	std::cout << "first parallel region\n";
	#pragma omp parallel private(i)
	{
		tid = omp_get_thread_num();
		x = 2*tid +1 ;
		std::cout << "tid = " << tid << " , x = " << x << "\n"; 


	}
	
 	std::cout << "second parallel region\n";
	#pragma omp parallel private(i)
	{
		std::cout << "tid = " << tid << " , x = " << x << "\n";

	} 
	
	std::cout << "after copyin operation\n";
	#pragma omp parallel copyin(x)  //copyin (copies: master thread to all other threads) can be used with threadprivate only
	{
	       std::cout << "tid = " << tid << " , x = " << x << "\n";		
	       //printf("tid: %d, x: %d\n", tid, x);	


	}	
}
