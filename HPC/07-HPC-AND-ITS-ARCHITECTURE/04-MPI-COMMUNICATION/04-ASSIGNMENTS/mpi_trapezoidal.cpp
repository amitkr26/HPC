/*
mpi_trapezoidal.cpp -- Section 2 (MPI), Problem 4: Parallel Trapezoidal Rule

Build (cluster):
    mpic++ -std=c++17 -O2 mpi_trapezoidal.cpp -o mpi_trapezoidal
Run (vary the process count to compare accuracy and runtime):
    mpirun -np 1 ./mpi_trapezoidal
    mpirun -np 2 ./mpi_trapezoidal
    mpirun -np 4 ./mpi_trapezoidal
    mpirun -np 8 ./mpi_trapezoidal
    mpirun -np 4 ./mpi_trapezoidal 2000000      (optional: different subinterval count)
sbatch:
    sbatch --nodes=1 --ntasks=8 --time=00:10:00 --wrap="mpirun -np 8 ./mpi_trapezoidal"

What it does:
  * Estimates the integral of f(x) = 4/(1+x^2) over [0,1], whose exact value is pi.
  * The interval is split into n trapezoids; the trapezoids are distributed over P
    processes with counts[r] = n/P + (r < n%P ? 1 : 0) so a NON-divisible n is
    handled. Each process computes only the sub-integral of its own contiguous
    sub-range (with the correct global step h = 1/n), results are combined with
    MPI_Reduce (MPI_SUM).
  * For each of several subinterval counts (10^2 .. 10^6, or argv override) it
    prints: integral, |error| vs pi, and the rank-max wall time, so you can
    compare accuracy and runtime for varying process counts and subintervals.
  * PASS: for the largest subinterval count the error must be within the
    composite-trapezoid bound (max(1e-8, 20/n^2)) and the error must shrink as
    n grows.
*/

#include <mpi.h>

#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <vector>

static const double kPi = 3.14159265358979323846;

static double f(double x)
{
    return 4.0 / (1.0 + x * x);
}

int main(int argc, char **argv)
{
    MPI_Init(&argc, &argv);

    int rank = 0, size = 1;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    std::vector<long long> ns;
    if (argc > 1) {
        ns.push_back(std::atoll(argv[1]));
    } else {
        long long base[] = {100, 1000, 10000, 100000, 1000000};
        for (int i = 0; i < 5; ++i) ns.push_back(base[i]);
    }

    for (size_t t = 0; t < ns.size(); ++t)
        if (ns[t] < (long long)size || ns[t] <= 0) {
            if (rank == 0)
                std::printf("ERROR: number of subintervals must be >= number of processes\n");
            MPI_Finalize();
            return 1;
        }

    if (rank == 0) {
        std::printf("=== Section 2.4 Parallel Trapezoidal Rule ===\n");
        std::printf("integral of 4/(1+x^2) over [0,1] = pi, P = %d, h = 1/n\n", size);
        std::printf("%12s %6s %20s %12s %10s %12s\n",
                    "subintervals", "div?", "integral", "|error|", "max ms", "err/n^2");
    }

    int status = 0;
    double prev_err = 1e300;
    bool monotone = true;
    double largest_err = 0.0;
    long long largest_n = 0;

    for (size_t t = 0; t < ns.size(); ++t) {
        long long n = ns[t];

        std::vector<int> counts((size_t)size), displs((size_t)size);
        int base = (int)(n / size);
        int rem = (int)(n % size);
        int off = 0;
        for (int i = 0; i < size; ++i) {
            counts[i] = base + (i < rem ? 1 : 0);
            displs[i] = off;
            off += counts[i];
        }

        double h = 1.0 / (double)n;
        int first = displs[rank];
        int cnt = counts[rank];

        MPI_Barrier(MPI_COMM_WORLD);
        double t0 = MPI_Wtime();

        double local = 0.0;
        for (int i = first; i < first + cnt; ++i) {
            double x0 = (double)i * h;
            double x1 = (double)(i + 1) * h;
            local += 0.5 * (f(x0) + f(x1)) * h;
        }

        double approx = 0.0;
        MPI_Reduce(&local, &approx, 1, MPI_DOUBLE, MPI_SUM, 0, MPI_COMM_WORLD);

        double t1 = MPI_Wtime();
        double my_time = t1 - t0, max_time = 0.0;
        MPI_Reduce(&my_time, &max_time, 1, MPI_DOUBLE, MPI_MAX, 0, MPI_COMM_WORLD);

        if (rank == 0) {
            double err = std::fabs(approx - kPi);
            if (err > prev_err) monotone = false;
            prev_err = err;
            if (t + 1 == ns.size()) { largest_err = err; largest_n = n; }
            std::printf("%12lld %6s %20.15f %12.3e %10.3f %12.3e\n",
                        n, n % size == 0 ? "yes" : "NO", approx, err,
                        1000.0 * max_time, err / ((double)n * (double)n));
        }
    }

    if (rank == 0) {
        double tol = 1e-8;
        double theoretical = 20.0 / ((double)largest_n * (double)largest_n);
        if (theoretical > tol) tol = theoretical;
        bool ok = largest_err <= tol && monotone;
        std::printf("largest n = %lld, error = %.3e (tol %.3e), error non-increasing: %s\n",
                    largest_n, largest_err, tol, monotone ? "yes" : "NO");
        std::printf("accuracy is set by n (same for every P); runtime should fall as P grows\n");
        std::printf("RESULT: %s\n", ok ? "PASS" : "FAIL");
        if (!ok) status = 1;
    }

    MPI_Bcast(&status, 1, MPI_INT, 0, MPI_COMM_WORLD);
    MPI_Finalize();
    return status;
}
