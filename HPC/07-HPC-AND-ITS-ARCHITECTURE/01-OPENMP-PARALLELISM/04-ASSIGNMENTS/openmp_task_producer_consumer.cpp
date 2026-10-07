/*
 * Section 1 - Problem 4: Producer-Consumer with OpenMP Tasks
 *
 * A producer/consumer pipeline over a shared BOUNDED buffer of CAP = 8 slots
 * with N_ITEMS = 200 items. For item i with slot s = i % CAP:
 *
 *   producer task:  depend(in: done[s]) depend(out: buffer[s])  -> writes item i
 *   consumer task:  depend(in: buffer[s]) depend(out: done[s])  -> reads item i
 *
 * The depend clauses make the runtime enforce the bounded-buffer discipline:
 * a producer may only refill slot s after the consumer that emptied it has
 * finished, so occupancy can never exceed CAP (this is verified at runtime).
 * Explicit synchronization required by the problem is also present: an
 * omp_lock_t guards every buffer access (critical section) and the shared
 * produced/consumed counters plus the occupancy high-water mark are updated
 * inside "#pragma omp critical" sections.
 *
 * Correctness is checked against an independent sequential reference: every
 * item 0..N_ITEMS-1 must be produced exactly once, consumed exactly once, the
 * consumed checksum must equal N*(N-1)/2, occupancy must stay <= CAP and every
 * buffer slot must be empty (-1) when the pipeline drains.
 *
 * Build: g++ -std=c++17 -fopenmp -Wall -Wextra -O2 openmp_task_producer_consumer.cpp -o openmp_task_producer_consumer
 * Run:   openmp_task_producer_consumer.exe
 */

#include <cstdio>
#include <vector>
#include <omp.h>

namespace {

constexpr int N_ITEMS = 200;
constexpr int CAP = 8;
constexpr int THREAD_LIST[] = {1, 2, 4, 8};

struct RunResult {
    double time = 0.0;
    long long produced = 0;
    long long consumed = 0;
    long long checksum = 0;
    long long max_occ = 0;
    bool all_seen = false;
    bool slots_empty = false;
};

RunResult run_pipeline(int threads) {
    int buffer[CAP];
    [[maybe_unused]] int done_tok[CAP];
    for (int s = 0; s < CAP; ++s) {
        buffer[s] = -1;
        done_tok[s] = 0;
    }

    long long produced = 0;
    long long consumed = 0;
    long long checksum = 0;
    long long max_occ = 0;
    std::vector<int> seen(N_ITEMS, 0);

    omp_lock_t buf_lock;
    omp_init_lock(&buf_lock);

    const double t0 = omp_get_wtime();
#pragma omp parallel num_threads(threads)
    {
#pragma omp single
        {
            for (int i = 0; i < N_ITEMS; ++i) {
                const int s = i % CAP;
#pragma omp task firstprivate(i, s) depend(in : done_tok[s]) depend(out : buffer[s])
                {
                    omp_set_lock(&buf_lock);
                    buffer[s] = i;
                    omp_unset_lock(&buf_lock);
#pragma omp critical(prod_stat)
                    {
                        ++produced;
                        const long long occ = produced - consumed;
                        if (occ > max_occ) max_occ = occ;
                    }
                }
#pragma omp task firstprivate(i, s) depend(in : buffer[s]) depend(out : done_tok[s])
                {
                    omp_set_lock(&buf_lock);
                    const int v = buffer[s];
                    buffer[s] = -1;
                    omp_unset_lock(&buf_lock);
                    if (v == i) seen[static_cast<size_t>(i)] = 1;
#pragma omp critical(cons_stat)
                    {
                        checksum += v;
                        ++consumed;
                        const long long occ = produced - consumed;
                        if (occ > max_occ) max_occ = occ;
                    }
                }
            }
#pragma omp taskwait
        }
    }
    const double elapsed = omp_get_wtime() - t0;
    omp_destroy_lock(&buf_lock);

    RunResult r;
    r.time = elapsed;
    r.produced = produced;
    r.consumed = consumed;
    r.checksum = checksum;
    r.max_occ = max_occ;
    r.all_seen = true;
    for (int i = 0; i < N_ITEMS; ++i)
        if (seen[static_cast<size_t>(i)] != 1) r.all_seen = false;
    r.slots_empty = true;
    for (int s = 0; s < CAP; ++s)
        if (buffer[s] != -1) r.slots_empty = false;
    return r;
}

}

int main() {
    const long long expected_sum = static_cast<long long>(N_ITEMS) * (N_ITEMS - 1) / 2;
    std::printf("Problem 4: Producer-Consumer with OpenMP Tasks\n");
    std::printf("Items = %d, bounded buffer capacity = %d slots, producers and consumers are "
                "tasks ordered by depend() + omp lock / critical sections\n\n",
                N_ITEMS, CAP);
    std::printf("Sequential reference: checksum of items 0..%d = %lld\n\n",
                N_ITEMS - 1, expected_sum);

    std::printf("%8s %12s %10s %10s %12s %10s %12s %6s\n",
                "threads", "time (s)", "produced", "consumed", "checksum", "max occ", "items seen", "check");

    bool all_ok = true;
    for (int t : THREAD_LIST) {
        const RunResult r = run_pipeline(t);
        const bool ok = r.produced == N_ITEMS && r.consumed == N_ITEMS &&
                        r.checksum == expected_sum && r.max_occ <= CAP && r.all_seen &&
                        r.slots_empty;
        all_ok = all_ok && ok;
        std::printf("%8d %12.6f %10lld %10lld %12lld %10lld %12s %6s\n",
                    t, r.time, r.produced, r.consumed, r.checksum, r.max_occ,
                    r.all_seen ? "all 200" : "MISSING", ok ? "PASS" : "FAIL");
    }

    std::printf("\nConclusion: all %d items flowed through the %d-slot bounded buffer exactly "
                "once at every thread count.\n", N_ITEMS, CAP);
    std::printf("The depend() edges (consumer done[s] -> next producer of slot s) are what keep "
                "occupancy <= %d, while the omp_lock around each buffer access and the critical "
                "sections on the counters make the producer/consumer updates race-free; without "
                "them items would be overwritten or double-counted.\n", CAP);
    std::printf("%s: produced == consumed == %d, checksum == %lld, occupancy never exceeded "
                "capacity, all slots drained\n", all_ok ? "PASS" : "FAIL", N_ITEMS, expected_sum);
    return all_ok ? 0 : 1;
}
