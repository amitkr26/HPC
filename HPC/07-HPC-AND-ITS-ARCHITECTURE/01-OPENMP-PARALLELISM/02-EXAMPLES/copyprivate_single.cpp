#include<iostream>
#include<omp.h>

int main(void)
{
	int a=125 , tid ;

	#pragma omp parallel num_threads(5) firstprivate(a) private(tid )
	{
		int tid = omp_get_thread_num();
		std::cout << "after firstprivate operation : tid = " << tid << " and a=" << a << "\n";
		
		#pragma omp barrier

		#pragma omp single copyprivate(a) //copyprivate (copies/broadcast value of one thread to all other threads):can be used with single only
		{ 
			a = a*2;
			std::cout << "in single block a =" << a << " , tid = " << tid << "\n";
		}
		
		std::cout << "after copyprivate a = " << a << " and tid = " << tid << "\n";
	}


}

//Assignment: try the same code without 'copyprivate'
