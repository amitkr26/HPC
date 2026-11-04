#include <mpi.h>
#include <iostream>

int main(int argc, char** argv)
{
    MPI_Init(&argc, &argv);

    int rank, size;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    // -------------------------
    // 1. MPI_Bcast
    // -------------------------
    int data = 0;

    if (rank == 0)
        data = 100;

    MPI_Bcast(&data, 1, MPI_INT, 0, MPI_COMM_WORLD);

    std::cout << "Rank " << rank
              << " received Bcast data = " << data << std::endl;


    // -------------------------
    // 2. MPI_Scatter
    // -------------------------
    int send_data[4] = {10, 20, 30, 40};
    int recv_data;

    MPI_Scatter(send_data, 1, MPI_INT,
                &recv_data, 1, MPI_INT,
                0, MPI_COMM_WORLD);

    std::cout << "Rank " << rank
              << " received Scatter data = " << recv_data << std::endl;


    // -------------------------
    // 3. MPI_Gather
    // -------------------------
    int gathered[4];

    MPI_Gather(&recv_data, 1, MPI_INT,
               gathered, 1, MPI_INT,
               0, MPI_COMM_WORLD);

    if (rank == 0)
    {
        std::cout << "Gathered data: ";

        for (int i = 0; i < size; i++)
            std::cout << gathered[i] << " ";

        std::cout << std::endl;
    }

    MPI_Finalize();
    return 0;
}

