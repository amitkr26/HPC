#include <mpi.h>
#include <iostream>

int main(int argc, char** argv)
{
    MPI_Init(&argc, &argv);

    int rank, size;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    // -------------------------
    // 1. MPI_Allgather
    // -------------------------
    int send_data = rank;
    int all_data[4];

    MPI_Allgather(&send_data, 1, MPI_INT,
                  all_data, 1, MPI_INT,
                  MPI_COMM_WORLD);

    std::cout << "Rank " << rank << " Allgather: ";

    for (int i = 0; i < size; i++)
        std::cout << all_data[i] << " ";

    std::cout << std::endl;


    // -------------------------
    // 2. MPI_Reduce
    // -------------------------
    int result;

    MPI_Reduce(&send_data, &result, 1, MPI_INT,
               MPI_SUM, 0, MPI_COMM_WORLD);

    if (rank == 0)
        std::cout << "Reduce sum = " << result << std::endl;


    // -------------------------
    // 3. MPI_Allreduce
    // -------------------------
    MPI_Allreduce(&send_data, &result, 1, MPI_INT,
                  MPI_SUM, MPI_COMM_WORLD);

    std::cout << "Rank " << rank
              << " Allreduce sum = " << result << std::endl;


    // -------------------------
    // 4. MPI_Reduce_scatter
    // -------------------------
    int send_array[4] = {1, 2, 3, 4};
    int recv_value;

    int recv_counts[4] = {1, 1, 1, 1};

    MPI_Reduce_scatter(send_array, &recv_value,
                       recv_counts, MPI_INT,
                       MPI_SUM, MPI_COMM_WORLD);

    std::cout << "Rank " << rank
              << " Reduce_scatter = " << recv_value << std::endl;

    MPI_Finalize();
    return 0;
}

