#include<iostream>

#include<omp.h>

int main(void)
{
	int sum=0 , i;

	#pragma omp parallel for reduction(+:sum) num_threads(4)
	//#pragma omp parallel for num_threads(4)
	for(i=1 ; i<=100 ; i++)
	{ 
		sum = sum + i;

	} 

	std::cout << "sum = " << sum << "\n";

}
