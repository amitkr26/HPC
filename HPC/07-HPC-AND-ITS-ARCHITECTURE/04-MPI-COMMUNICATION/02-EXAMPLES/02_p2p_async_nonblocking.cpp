// 2_p2p_async.cpp
// -----------------------------------------------------------------
// POINT-TO-POINT, ASYNCHRONOUS (non-blocking)
//
// Rank 0 and rank 1 EXCHANGE data with each other at the same time
// using MPI_Isend / MPI_Irecv. Both calls return immediately, so
// each rank can post its send and receive back-to-back without
// worrying about ordering, then do independent work, then
// MPI_Wait for completion. This pattern also avoids the deadlock
// risk you would have if both ranks called the blocking MPI_Send
// first (each waiting for the other to receive).
//
// Run with exactly 2 ranks: mpirun -np 2 ./2_p2p_async
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
    const int TAG = 7;
    int partner = 1 - rank;

    std::vector<double> send_buf(N), recv_buf(N);
    for (int i = 0; i < N; ++i) send_buf[i] = (rank + 1) * 10.0 + i;

    MPI_Request requests[2];

    // Post both operations without waiting -- this is the "async" part.
    MPI_Isend(send_buf.data(), N, MPI_DOUBLE, partner, TAG, MPI_COMM_WORLD, &requests[0]);
    MPI_Irecv(recv_buf.data(), N, MPI_DOUBLE, partner, TAG, MPI_COMM_WORLD, &requests[1]);

    // --- communication is now happening in the background ---
    printf("[rank %d] Isend/Irecv posted, doing other work while they complete...\n", rank);
    volatile double busy = 0;
    for (int i = 0; i < 1000000; ++i) busy += i * 0.000001; // stand-in for real computation

    // Block here only until both requests finish.
    MPI_Waitall(2, requests, MPI_STATUSES_IGNORE);

    printf("[rank %d] received from rank %d: ", rank, partner);
    for (double v : recv_buf) printf("%.1f ", v);
    printf("\n");

    MPI_Finalize();
    return 0;
}
