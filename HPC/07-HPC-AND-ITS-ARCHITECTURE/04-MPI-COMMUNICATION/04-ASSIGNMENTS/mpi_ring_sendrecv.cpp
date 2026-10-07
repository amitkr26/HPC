/*
mpi_ring_sendrecv.cpp -- Section 2 (MPI), Problem 3: Ring-Based Message Passing

Build (cluster):
    mpic++ -std=c++17 -O2 mpi_ring_sendrecv.cpp -o mpi_ring_sendrecv
Run (SAFE default -- uses MPI_Sendrecv, never deadlocks):
    mpirun -np 8 ./mpi_ring_sendrecv
Deadlock demonstration (blocking Send/Recv; WILL HANG -- only entered via flag):
    timeout 15 mpirun -np 8 ./mpi_ring_sendrecv --deadlock
sbatch:
    sbatch --nodes=1 --ntasks=8 --time=00:05:00 --wrap="mpirun -np 8 ./mpi_ring_sendrecv"

What it does:
  * Every rank starts with value (rank+1). In a ring, each rank sends its current
    message to the RIGHT neighbour and receives the message of its LEFT neighbour
    with MPI_Sendrecv, forwarding what it received and accumulating it into a
    running total. After P-1 circulations every rank holds the sum 1+2+...+P.
  * Correctness: MPI_Allreduce of the per-rank totals with MPI_MIN and MPI_MAX;
    PASS requires min == max == P*(P+1)/2 (every rank agreed) and the per-rank
    totals are printed.
  * The DEADLOCK-PRONE version (blocking MPI_Send to the right neighbour first,
    then MPI_Recv from the left) is completely separated: it runs only when the
    program is started with the --deadlock flag. It sends a large message
    (bigger than the eager-transport buffer) so every rank blocks inside
    MPI_Send with no matching receive posted anywhere -> the ring deadlocks.
    A default run therefore never hangs. np must be >= 2 for the demo.
*/

#include <mpi.h>

#include <cstdio>
#include <cstdlib>
#include <string>
#include <vector>

static const int kTag = 42;
static const int kBigCount = 262144;

int main(int argc, char **argv)
{
    bool demo_deadlock = false;
    for (int i = 1; i < argc; ++i)
        if (std::string(argv[i]) == "--deadlock") demo_deadlock = true;

    MPI_Init(&argc, &argv);

    int rank = 0, size = 1;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    int right = (rank + 1) % size;
    int left = (rank - 1 + size) % size;

    if (demo_deadlock) {
        if (rank == 0) {
            std::printf("=== DEADLOCK DEMONSTRATION: blocking MPI_Send / MPI_Recv ===\n");
            std::printf("Every rank first does a BLOCKING MPI_Send of %d ints (%d KB,\n",
                        kBigCount, kBigCount * 4 / 1024);
            std::printf("larger than any eager buffer) to its right neighbour, and only\n");
            std::printf("afterwards posts MPI_Recv from its left neighbour. Because every\n");
            std::printf("rank is stuck inside MPI_Send, no receive is ever posted and the\n");
            std::printf("whole ring blocks forever: DEADLOCK. If the program does not print\n");
            std::printf("'no deadlock observed', it is hanging right now -- kill it\n");
            std::printf("(Ctrl-C, or run under 'timeout 15').\n");
            std::fflush(stdout);
        }
        if (size < 2) {
            if (rank == 0)
                std::printf("np == 1: a ring has no neighbours, deadlock demo skipped.\n");
        } else {
            std::vector<int> big((size_t)kBigCount, rank);
            std::printf("rank %d: about to blocking-Send %d ints to rank %d ...\n",
                        rank, kBigCount, right);
            std::fflush(stdout);
            MPI_Send(big.data(), kBigCount, MPI_INT, right, kTag, MPI_COMM_WORLD);
            std::printf("rank %d: send completed (unexpected -- buffered?)\n", rank);
            MPI_Recv(big.data(), kBigCount, MPI_INT, left, kTag, MPI_COMM_WORLD,
                     MPI_STATUS_IGNORE);
            std::printf("rank %d: ring round-tripped without hanging\n", rank);
            std::fflush(stdout);
        }
        MPI_Finalize();
        return 0;
    }

    if (rank == 0) {
        std::printf("=== Section 2.3 Ring-Based Message Passing (MPI_Sendrecv) ===\n");
        std::printf("P = %d; each rank sends to (rank+1)%%P and receives from (rank-1)%%P\n",
                    size);
        std::printf("each rank starts with %d; the message circulates P-1 times\n", 1);
    }

    int msg = rank + 1;
    long long total = msg;
    int recv = 0;

    MPI_Barrier(MPI_COMM_WORLD);
    double t0 = MPI_Wtime();

    for (int step = 1; step < size; ++step) {
        MPI_Sendrecv(&msg, 1, MPI_INT, right, kTag,
                     &recv, 1, MPI_INT, left, kTag,
                     MPI_COMM_WORLD, MPI_STATUS_IGNORE);
        msg = recv;
        total += msg;
    }

    double t1 = MPI_Wtime();

    long long mn = 0, mx = 0;
    MPI_Allreduce(&total, &mn, 1, MPI_LONG_LONG, MPI_MIN, MPI_COMM_WORLD);
    MPI_Allreduce(&total, &mx, 1, MPI_LONG_LONG, MPI_MAX, MPI_COMM_WORLD);

    std::vector<long long> totals((size_t)size, 0);
    MPI_Gather(&total, 1, MPI_LONG_LONG,
               totals.data(), 1, MPI_LONG_LONG, 0, MPI_COMM_WORLD);

    long long expected = (long long)size * (long long)(size + 1) / 2;
    int ok = (mn == expected && mx == expected) ? 1 : 0;

    if (rank == 0) {
        std::printf("per-rank accumulated totals:\n");
        for (int i = 0; i < size && i < 16; ++i) std::printf("  rank %d: %lld\n", i, totals[(size_t)i]);
        if (size > 16) std::printf("  ...\n");
        std::printf("min total = %lld, max total = %lld, expected = %lld\n", mn, mx, expected);
        std::printf("ring circulation time = %.3f ms\n", 1000.0 * (t1 - t0));
        std::printf("RESULT: %s\n", ok ? "PASS" : "FAIL");
    }

    int status = ok ? 0 : 1;
    MPI_Bcast(&status, 1, MPI_INT, 0, MPI_COMM_WORLD);
    MPI_Finalize();
    return status;
}
