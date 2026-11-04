#include <mpi.h>
#include <iostream>

int main(int argc, char** argv)
{
    MPI_Init(&argc, &argv);

    int rank, size;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    int send_data[4];
    int recv_data[4];

    // Each rank prepares one value for every rank
    for (int i = 0; i < size; i++)
        send_data[i] = rank * 10 + i;

    MPI_Alltoall(send_data, 1, MPI_INT,
                 recv_data, 1, MPI_INT,
                 MPI_COMM_WORLD);

    std::cout << "Rank " << rank << " received: ";

    for (int i = 0; i < size; i++)
        std::cout << recv_data[i] << " ";

    std::cout << std::endl;

    MPI_Finalize();
    return 0;
}

