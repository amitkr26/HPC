// 1_p2p_sync.cpp
// -----------------------------------------------------------------
// POINT-TO-POINT, SYNCHRONOUS (blocking)
//
// Rank 0 sends an array of doubles to rank 1 using MPI_Ssend.
// MPI_Ssend ("synchronous send") does not return until the matching
// MPI_Recv on rank 1 has actually started receiving the message —
// this is the clearest way to demonstrate true synchronous
// hand-off between two processes (vs. MPI_Send, which is blocking
// but may return early because the implementation buffered the
// message).
//
// Run with exactly 2 ranks: mpirun -np 2 ./1_p2p_sync
// -----------------------------------------------------------------
#include <mpi.h>
#include <cstdio>
#include <vector>

int main(int argc, char** argv) {
    MPI_Init(&argc, &argv);

    int rank, size;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    if (size != 2) {
        if (rank == 0)
            fprintf(stderr, "This demo needs exactly 2 ranks (got %d)\n", size);
        MPI_Finalize();
        return 1;
    }

    const int N = 5;
    const int TAG = 42;

    if (rank == 0) {
        std::vector<double> data(N);
        for (int i = 0; i < N; ++i) data[i] = i * 1.5;

        printf("[rank 0] MPI_Ssend -> rank 1 (blocks until rank 1 is receiving)\n");
        MPI_Ssend(data.data(), N, MPI_DOUBLE, /*dest=*/1, TAG, MPI_COMM_WORLD);
        printf("[rank 0] send complete, rank 1 has the data\n");

    } else { // rank == 1
        std::vector<double> buf(N);
        MPI_Status status;

        printf("[rank 1] about to MPI_Recv from rank 0 ...\n");
        MPI_Recv(buf.data(), N, MPI_DOUBLE, /*source=*/0, TAG, MPI_COMM_WORLD, &status);

        printf("[rank 1] received: ");
        for (double v : buf) printf("%.1f ", v);
        printf("\n");
    }

    MPI_Finalize();
    return 0;
}
