# Profiling exercises (module 09)

Sample programs and tool setup captured from the profiling session. The
original drop was a 27 MB Intel VTune result bundle (`program.zip`) — the
profiler databases (`.vtune`, `sqlite-db/timelinedb`, `r001hs`…`r007hs`) were
deliberately **not** committed; only the reproducible source is kept here.

## Files

| File | Purpose |
|------|---------|
| `test1.c` | Busy-loop sample: `main()` → `func1()` → `new_func1()` (external) → `func2()` (static). Each routine spins on a different loop bound so a profiler can rank them by self time. |
| `test2.c` | Definition of `new_func1()` — link with `test1.c` (`gcc test1.c test2.c`) to resolve the forward declaration. |
| `setupscript.sh` | Exports the TAU 2.33.1 and binutils 2.41.90 paths, then exposes `tau_exec` and `gprofng`. |

## Build and run

```bash
gcc -O0 -g test1.c test2.c -o test      # keep -O0 so the loops are not optimized away
./test
```

> **Use `-O0`.** The loops compare a signed `int i` against constants such as
> `0xffffffff`, so the counter has to wrap through negative values before the
> test fails. At `-O0` that works and the program exits after ~2^32 iterations
> (about a minute). With `-O2` GCC reports
> `iteration 2147483647 invokes undefined behavior [-Waggressive-loop-optimizations]`
> and the optimized loop never terminates — the run is killed instead of exiting.

Expected output (order matters — `new_func1` is called from `func1`):

```
 Inside main()
  Inside func1
 Inside new_func1()
 Inside func2
```

## Profile

```bash
source ./setupscript.sh      # puts tau_exec and gprofng on PATH
gprofng display text ./test  # gprofng (binutils) hotspot report
tau_exec ./test              # TAU annotation-free run
```

`test1.c` loops up to `0xffffff`, `0xffffffff`, `0xffffffaa` and `0xffffffee`
iterations respectively, so `func1` (via `new_func1`) dominates the profile —
that is the intended result: the tool should report `new_func1` and `func1`
as the hotspots, `main` next, and `func2` last.
