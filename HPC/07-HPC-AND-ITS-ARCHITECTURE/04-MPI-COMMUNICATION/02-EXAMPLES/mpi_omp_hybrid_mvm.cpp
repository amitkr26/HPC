// y = A*x with A distributed by columns across MPI ranks (OpenMP inside each rank).
//
// Build:  mpicxx -O3 -fopenmp mpi_omp_fmvm.cpp -o mpi_omp_fmvm
// Run:    see the commands in the reply (2 nodes, 1 rank per node, all cores)
// Optional argument: n (default 100000), e.g. ./mpi_omp_fmvm 8000 for quick tests

#include <mpi.h>
#include <omp.h>
#include <cstdio>
#include <cstdlib>
#include <cmath>
#include <vector>

int main(int argc, char **argv)
{
    const int root = 0;
    int n = 100000;                             
    if (argc > 1) n = std::atoi(argv[1]);

    // Use all cores unless the user set OMP_NUM_THREADS (replaces hard-coded 48)
    if (!std::getenv("OMP_NUM_THREADS"))
        omp_set_num_threads(omp_get_num_procs());

    MPI_Init(&argc, &argv);
    int rank, size;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    if (n % size != 0) {
        if (rank == root)
            std::printf("Number of elements not divisible by number of processes\n");
        MPI_Finalize();
        return 1;
    }

    int chunk_size = n / size;
    int j_start = rank * chunk_size + 1;         

    // Report where each rank runs and how many threads it will use
    char host[MPI_MAX_PROCESSOR_NAME];
    int hlen;
    MPI_Get_processor_name(host, &hlen);
    std::printf("rank %d/%d on %s: %d OpenMP threads\n",
                rank, size, host, omp_get_max_threads());
    std::fflush(stdout);

    // Local part of A (column-major)
    // local part of x, and this rank's partial y. size_t: n*chunk_size exceeds int range.
    std::vector<double> local_A((size_t)n * chunk_size);
    std::vector<double> local_x(chunk_size);
    std::vector<double> local_y(n, 0.0);

    for (int j = 0; j < chunk_size; j++) {
        local_x[j] = (double)(j_start + j);
        for (int i = 0; i < n; i++)
            local_A[(size_t)j * n + i] = 1.0;
    }

    std::vector<double> y;
    double t_start = 0.0, t_end = 0.0;
    if (rank == root) {
        y.resize(n);
        t_start = omp_get_wtime();
    }

    // Local matrix-vector product; each thread accumulates into a private copy of y
    const double *A = local_A.data();
    const double *x = local_x.data();
    double *ly = local_y.data();
    #pragma omp parallel for reduction(+:ly[:n])
    for (int j = 0; j < chunk_size; j++) {
        for (int i = 0; i < n; i++)
            ly[i] += A[(size_t)j * n + i] * x[j];
    }

    MPI_Barrier(MPI_COMM_WORLD);

    // Sum all partial vectors into y on the root
    MPI_Reduce(local_y.data(), rank == root ? y.data() : nullptr,
               n, MPI_DOUBLE, MPI_SUM, root, MPI_COMM_WORLD);

    int status = 0;
    if (rank == root) {
        t_end = omp_get_wtime();
        double expected = (double)n * (double)(n + 1) / 2.0;

        // Correctness: every element of y must equal n(n+1)/2
        long bad = 0;
        for (int i = 0; i < n; i++)
            if (std::fabs(y[i] - expected) > 1e-12 * expected) bad++;

        std::printf("runtime(ms): %f\n", 1000.0 * (t_end - t_start));
        std::printf("Result vector y = A*x :\n");
        std::printf("y(1) = %.1f\n", y[0]);
        std::printf("y(%d) = %.1f\n", n, y[n - 1]);
        std::printf("Expected result for any element of y: %.1f\n", expected);
        std::printf("Correctness: %s (%ld mismatches out of %d elements)\n",
                    bad == 0 ? "PASS" : "FAIL", bad, n);
        if (bad != 0) status = 2;
    }

    MPI_Finalize();
    return status;
}

