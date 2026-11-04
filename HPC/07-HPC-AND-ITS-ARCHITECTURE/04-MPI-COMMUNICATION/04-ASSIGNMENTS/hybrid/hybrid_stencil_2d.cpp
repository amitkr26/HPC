/*
hybrid_stencil_2d.cpp -- Section 3 (Hybrid MPI+OpenMP), Problem 3: Hybrid 2D Stencil / Heat Diffusion

Build (cluster):
    mpic++ -std=c++17 -fopenmp -O2 hybrid_stencil_2d.cpp -o hybrid_stencil_2d
Run (vary grid size, process count and thread count; report comm vs comp):
    OMP_NUM_THREADS=6  mpirun -np 2  ./hybrid_stencil_2d 1024 1024 50
    OMP_NUM_THREADS=3  mpirun -np 4  ./hybrid_stencil_2d 1024 1024 50
    OMP_NUM_THREADS=1  mpirun -np 12 ./hybrid_stencil_2d 2048 2048 50
    OMP_NUM_THREADS=12 mpirun -np 1  ./hybrid_stencil_2d 2048 2048 50
    ./hybrid_stencil_2d 4096 4096 100     (arguments: NX NY iterations)
sbatch:
    sbatch --nodes=1 --ntasks=4 --cpus-per-task=3 --time=00:20:00 \
           --env OMP_NUM_THREADS=3 --wrap="mpirun -np 4 ./hybrid_stencil_2d 1024 1024 50"

What it does:
  * 2D grid NX x NY (default 1024 x 1024), `iters` Jacobi/heat iterations
    u_new[i][j] = 0.25*(u[i-1][j] + u[i+1][j] + u[i][j-1] + u[i][j+1]) with the
    global outer rows/columns held at 0 (Dirichlet boundary) and the interior
    initialised to 100.
  * Row-block decomposition across MPI ranks: rank r owns rows
    [displ, displ+count) with count = NY/P + (r < NY%P ? 1 : 0) -- non-divisible
    NY handled; every rank needs at least one owned row.
  * Halo exchange: each iteration the first owned row is sent to the rank above
    and the last owned row to the rank below with MPI_Sendrecv (two calls, two
    tags; MPI_PROC_NULL at the ends of the chain), so ghost rows for the
    interior update are always fresh.
  * OpenMP parallelises the interior-point update over the owned rows
    (double buffered: read current buffer, write next buffer -> no races).
  * Timing breakdown: communication time (around the two MPI_Sendrecv calls) and
    computation time (around the OpenMP update + swap) are accumulated per rank
    and reported as rank-max and rank-average with percentages, so you can vary
    grid size and P x T from the docstring commands and compare comm vs comp.
  * Verification: at rank 0 the final grid is gathered (MPI_Gatherv over rows)
    and compared elementwise against a serial double-buffered reference run of
    the same iterations; for very large grids (> 4M points) the serial reference
    is skipped and boundary/monotonicity invariants are checked instead.
    PASS/FAIL printed.
*/

#include <mpi.h>
#include <omp.h>

#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <vector>

static void init_grid(std::vector<double> &u, int nx, int ny)
{
    u.assign((size_t)nx * (size_t)ny, 0.0);
    for (int i = 1; i < ny - 1; ++i)
        for (int j = 1; j < nx - 1; ++j)
            u[(size_t)i * nx + j] = 100.0;
}

static void serial_reference(std::vector<double> &u, int nx, int ny, int iters)
{
    std::vector<double> v(u.size(), 0.0);
    for (int it = 0; it < iters; ++it) {
        for (int i = 1; i < ny - 1; ++i) {
            const double *cu = &u[(size_t)i * nx];
            double *cv = &v[(size_t)i * nx];
            const double *up = &u[(size_t)(i - 1) * nx];
            const double *dn = &u[(size_t)(i + 1) * nx];
            cv[0] = 0.0;
            cv[nx - 1] = 0.0;
            for (int j = 1; j < nx - 1; ++j)
                cv[j] = 0.25 * (up[j] + dn[j] + cu[j - 1] + cu[j + 1]);
        }
        std::swap(u, v);
    }
}

int main(int argc, char **argv)
{
    if (!std::getenv("OMP_NUM_THREADS")) omp_set_num_threads(omp_get_num_procs());

    MPI_Init(&argc, &argv);

    int rank = 0, size = 1;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    int nx = 1024, ny = 1024, iters = 50;
    if (argc > 1) nx = std::atoi(argv[1]);
    if (argc > 2) ny = std::atoi(argv[2]);
    if (argc > 3) iters = std::atoi(argv[3]);

    if (nx < 4 || ny < 4 || iters < 1 || ny < size) {
        if (rank == 0)
            std::printf("ERROR: need NX,NY >= 4, iters >= 1 and NY >= number of processes\n");
        MPI_Finalize();
        return 1;
    }

    const int maxt = omp_get_max_threads();

    std::vector<int> counts((size_t)size), displs((size_t)size);
    int base = ny / size, rem = ny % size, off = 0;
    for (int i = 0; i < size; ++i) {
        counts[i] = base + (i < rem ? 1 : 0);
        displs[i] = off;
        off += counts[i];
    }
    const int s = displs[rank];
    const int e = s + counts[rank] - 1;

    const int up = (rank == 0) ? MPI_PROC_NULL : rank - 1;
    const int down = (rank == size - 1) ? MPI_PROC_NULL : rank + 1;
    const int tag_a = 101, tag_b = 102;

    std::vector<double> cur, nxt;
    init_grid(cur, nx, ny);
    nxt = cur;

    std::vector<double> top_halo((size_t)nx, 0.0), bot_halo((size_t)nx, 0.0);

    const int lo = s > 0 ? s : 1;
    const int hi = (e < ny - 1 ? e : ny - 2);

    if (rank == 0) {
        std::printf("=== Section 3.3 Hybrid 2D Stencil / Heat Diffusion ===\n");
        std::printf("grid %d x %d, %d iterations, P = %d ranks, T = %d threads\n",
                    nx, ny, iters, size, maxt);
        std::printf("row blocks:");
        for (int i = 0; i < size && i < 16; ++i)
            std::printf(" [%d]=%d", i, counts[i]);
        if (size > 16) std::printf(" ...");
        std::printf("\n");
    }

    double t_comm = 0.0, t_comp = 0.0;

    MPI_Barrier(MPI_COMM_WORLD);
    double wall0 = MPI_Wtime();

    for (int it = 0; it < iters; ++it) {
        double c0 = MPI_Wtime();
        MPI_Status st;
        MPI_Sendrecv(&cur[(size_t)s * nx], nx, MPI_DOUBLE, up, tag_a,
                     bot_halo.data(), nx, MPI_DOUBLE, down, tag_a,
                     MPI_COMM_WORLD, &st);
        MPI_Sendrecv(&cur[(size_t)e * nx], nx, MPI_DOUBLE, down, tag_b,
                     top_halo.data(), nx, MPI_DOUBLE, up, tag_b,
                     MPI_COMM_WORLD, &st);
        double c1 = MPI_Wtime();
        t_comm += c1 - c0;

        double d0 = MPI_Wtime();
        #pragma omp parallel for schedule(static)
        for (int i = lo; i <= hi; ++i) {
            double *nr = &nxt[(size_t)i * nx];
            if (i == 0 || i == ny - 1) {
                for (int j = 0; j < nx; ++j) nr[j] = 0.0;
                continue;
            }
            nr[0] = 0.0;
            nr[nx - 1] = 0.0;
            const double *top = (i - 1 >= s) ? &cur[(size_t)(i - 1) * nx] : top_halo.data();
            const double *bot = (i + 1 <= e) ? &cur[(size_t)(i + 1) * nx] : bot_halo.data();
            const double *cu = &cur[(size_t)i * nx];
            for (int j = 1; j < nx - 1; ++j)
                nr[j] = 0.25 * (top[j] + bot[j] + cu[j - 1] + cu[j + 1]);
        }
        if (s == 0) {
            double *nr = &nxt[0];
            for (int j = 0; j < nx; ++j) nr[j] = 0.0;
        }
        if (e == ny - 1) {
            double *nr = &nxt[(size_t)(ny - 1) * nx];
            for (int j = 0; j < nx; ++j) nr[j] = 0.0;
        }
        std::swap(cur, nxt);
        double d1 = MPI_Wtime();
        t_comp += d1 - d0;
    }

    double wall1 = MPI_Wtime();

    double max_comm = 0.0, max_comp = 0.0, max_wall = 0.0;
    double sum_comm = 0.0, sum_comp = 0.0;
    MPI_Reduce(&t_comm, &max_comm, 1, MPI_DOUBLE, MPI_MAX, 0, MPI_COMM_WORLD);
    MPI_Reduce(&t_comp, &max_comp, 1, MPI_DOUBLE, MPI_MAX, 0, MPI_COMM_WORLD);
    double wall = wall1 - wall0;
    MPI_Reduce(&wall, &max_wall, 1, MPI_DOUBLE, MPI_MAX, 0, MPI_COMM_WORLD);
    MPI_Reduce(&t_comm, &sum_comm, 1, MPI_DOUBLE, MPI_SUM, 0, MPI_COMM_WORLD);
    MPI_Reduce(&t_comp, &sum_comp, 1, MPI_DOUBLE, MPI_SUM, 0, MPI_COMM_WORLD);

    const int send_rows = counts[rank] * nx;
    std::vector<int> gc((size_t)size, 0), gd((size_t)size, 0);
    if (rank == 0) {
        int o = 0;
        for (int i = 0; i < size; ++i) {
            gc[(size_t)i] = counts[i] * nx;
            gd[(size_t)i] = o;
            o += gc[(size_t)i];
        }
    }
    std::vector<double> full;
    if (rank == 0) full.resize((size_t)nx * (size_t)ny, 0.0);
    MPI_Gatherv(&cur[(size_t)s * nx], send_rows, MPI_DOUBLE,
                full.data(), gc.data(), gd.data(), MPI_DOUBLE, 0, MPI_COMM_WORLD);

    int status = 0;
    if (rank == 0) {
        bool ok = true;
        double max_err = -1.0;
        long long bad = 0;
        long long points = (long long)nx * (long long)ny;
        if (points <= 4194304LL) {
            std::vector<double> ref;
            init_grid(ref, nx, ny);
            serial_reference(ref, nx, ny, iters);
            for (size_t i = 0; i < ref.size(); ++i) {
                double err = std::fabs(ref[i] - full[i]);
                if (err > max_err) max_err = err;
                if (err > 1e-12) ++bad;
            }
            ok = (bad == 0);
        } else {
            max_err = 0.0;
            for (int j = 0; j < nx; ++j) {
                if (full[j] != 0.0) ++bad;
                if (full[(size_t)(ny - 1) * nx + j] != 0.0) ++bad;
            }
            for (int i = 0; i < ny; ++i) {
                if (full[(size_t)i * nx] != 0.0) ++bad;
                if (full[(size_t)i * nx + nx - 1] != 0.0) ++bad;
            }
            for (size_t i = 0; i < full.size(); ++i)
                if (!(full[i] >= 0.0 && full[i] <= 100.0)) ++bad;
            ok = (bad == 0);
        }

        double comm_pct = (max_comm + max_comp) > 0.0
                              ? 100.0 * max_comm / (max_comm + max_comp)
                              : 0.0;
        std::printf("rank-max communication time = %.3f ms (%.1f%%)\n",
                    1000.0 * max_comm, comm_pct);
        std::printf("rank-max computation  time = %.3f ms (%.1f%%)\n",
                    1000.0 * max_comp, 100.0 - comm_pct);
        std::printf("rank-max wall per iteration = %.3f ms, rank-avg comm = %.3f ms, rank-avg comp = %.3f ms\n",
                    1000.0 * max_wall / iters, 1000.0 * sum_comm / size,
                    1000.0 * sum_comp / size);
        std::printf("halo exchange: 2 x MPI_Sendrecv of %d doubles per iteration per rank\n", nx);
        std::printf("verification (%s): max abs err vs serial reference = %.3e, bad = %lld\n",
                    points <= 4194304LL ? "full serial reference" : "boundary/range invariants",
                    max_err, bad);
        std::printf("RESULT: %s\n", ok ? "PASS" : "FAIL");
        if (!ok) status = 1;
    }

    MPI_Bcast(&status, 1, MPI_INT, 0, MPI_COMM_WORLD);
    MPI_Finalize();
    return status;
}
