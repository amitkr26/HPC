#include<iostream>
#include<omp.h>

int main()
{
	int variable = 5;

	//#pragma omp parallel num_threads(4), private(variable) 
	//#pragma omp parallel num_threads(4), private(variable), firstprivate(variable) //error: ‘variable’ appears more than once in data clauses 
	#pragma omp parallel num_threads(4), firstprivate(variable)  
	{
		std::cout << "in parallel region: variable: " << variable << "\n";
	}

	std::cout << "in serial region: variable: " << variable << "\n";
	
	return(0);
}
