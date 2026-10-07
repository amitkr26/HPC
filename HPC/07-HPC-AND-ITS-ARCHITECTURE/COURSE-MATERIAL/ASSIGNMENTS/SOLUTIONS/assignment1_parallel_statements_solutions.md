# Assignment 1 — Can these statements be executed in parallel?

Solutions for `../assignment1_parallel_statements.pdf`.

Source: `../parallel_programming_lecture.pdf` (deck page 77 carries Exercise 17).

## Notation

| Symbol | Meaning |
|--------|---------|
| **RAW** | flow / true dependence — the second statement *reads* what the first *wrote* |
| **WAR** | anti-dependence — the second statement *writes* a location the first *read* |
| **WAW** | output dependence — both statements *write* the same location |
| YES | safe to run concurrently and produce the same result |
| NO | order must be preserved |

Two statements are independent (→ parallel) only when they share **no** memory
location in a read/write pair. Sharing a location is fine only if at least one
access is a read *and* the writes target different locations.

---

## Exercise 1 — `a=1; b=2;`

**YES.** `a` and `b` are different variables. Write–write to distinct addresses,
no read of either. Fully independent; either order gives the same final state.

## Exercise 2 — `a=1; b=a;`

**NO — RAW (flow) dependence.** Line 2 reads `a`, which line 1 defines. If
`b = a` runs first it captures the *old* value of `a`, not `1`.

```
serial:   a=1  then  b=a      → a=1, b=1
parallel: b=a  first          → a=1, b=old_a   ✗
```

## Exercise 3 — `b = a; a = 1;`

**NO — WAR (anti-) dependence.** Line 1 *reads* `a`, line 2 *writes* it. The
read must happen before the write, otherwise `b` picks up `1` instead of the
previous contents of `a`.

This is the mirror image of Exercise 2: there the read was second, here it is
first. Either way the pair is ordered.

## Exercise 4 — `a = 1; a = 2;`

**NO — WAW (output) dependence.** Both statements write `a`. The final value
must be `2`, so `a = 2` must be the last writer. If they race, `a` may end up
`1`.

Note this is a *pure* write–write conflict — there is no read involved at all,
yet it is still order-dependent, because the result of the whole block is
defined by which store lands last.

## Exercise 5 — `for(i=0;i<100;i++) a[i] = i`

**YES.** Each iteration writes `a[i]` for a *distinct* `i`, and nothing is read.
Iteration `i` and iteration `j` touch different addresses (`i ≠ j`), so there is
no loop-carried dependence of any kind. This is the textbook case for
`#pragma omp parallel for`.

## Exercise 7 — `for(i=0;i<100;i++) { a[i] = i; b[i] = 2*i; }`

**YES.** The body writes one element of `a` and one element of `b`, both indexed
by the loop variable. Across iterations the written addresses are always
distinct, and no location is ever read. Loop iterations are mutually
independent.

(Exercise 6 is missing from the source sheet — it jumps from 5 to 7.)

## Exercise 8 — two separate loops over `a[]` then `b[]`

```c
for(i=0;i<100;i++) a[i] = i;
for(i=0;i<100;i++) b[i] = 2*i;
```

**YES — in two ways.**

1. Each individual loop is independent, exactly as in Exercise 5.
2. The two loops are *also* independent of each other: loop 1 writes only `a`,
   loop 2 writes only `b`. They have no memory location in common, so even the
   two loop bodies could be overlapped.

This is the only exercise where both the intra-loop *and* inter-loop
parallelism are visible.

## Exercise 9 — `for(i=0;i<100;i++) a[i] = a[i] + 100;`

**YES.** Every iteration reads **and** writes the *same* index `a[i]`, but that
index is unique to the iteration. The read and the write belong to the same
iteration, not to different ones, so no loop-carried dependence exists.

The read-modify-write looks dangerous at a glance — it is not, as long as the
addresses do not overlap between iterations. Contrast with Exercise 10, where
the read uses a *different* index than the write.

## Exercise 10 — `for(i=0;i<100;i++) a[i] = f(a[i-1]);`

**NO — loop-carried RAW dependence with distance 1.**

Iteration `i` reads `a[i-1]`, which was written by iteration `i-1`. The value
propagates down the whole array:

```
a[1] = f(a[0]) → a[2] = f(a[1]) → a[3] = f(a[2]) → …
```

This is a **sequential prefix** (scan). It cannot be parallelised as written.
Standard escape hatches, none of which are free:

- **Blelloch / Hillis-Steele scan** — O(log n) parallel depth at the cost of
  extra temporary storage and more total work.
- If `f` is associative and you only need `a[n-1]`, a tree reduction suffices.
- If `f` is the identity, the whole loop is a no-op.

## Exercise 11 — row-major nest, inner dependence on `j`

```c
for(i=0;i<100;i++)
  for(j=0;j<100;j++)
    a[i][j] = f(a[i][j-1]);
```

**YES over `i` (the outer loop); NO over `j` (the inner loop).**

The recurrence `a[i][j] ← f(a[i][j-1])` is a *within-row* prefix: it forces
`j = 0,1,2,…` to run in order **for a fixed row `i`**.

But different rows never touch the same addresses — row `i` reads only
`a[i][*]`, row `k` reads only `a[k][*]`. So the 100 rows are fully independent
and the **outer** loop parallelises:

```c
#pragma omp parallel for collapse(1)
for (i = 0; i < 100; i++)
    for (j = 0; j < 100; j++)          // serial — carries the recurrence
        a[i][j] = f(a[i][j-1]);
```

`collapse(2)` would be wrong here: it would parallelise `j` too and destroy
the ordering the recurrence needs.

## Exercise 12 — column-major nest (loops swapped)

```c
for(j=0;j<100;j++)
  for(i=0;i<100;i++)
    a[i][j] = f(a[i][j-1]);
```

**YES over `i` (the inner loop); NO over `j` (the outer loop).**

Same computation as Exercise 11, different traversal order — and that flips
which loop is safe:

- The outer `j` iteration reads column `j-1` and writes column `j`, so column
  passes **must** stay ordered → outer loop serial.
- Within one `j` pass, all 100 values of `i` read `a[i][j-1]`, which the
  previous pass already finished writing. Those 100 accesses touch distinct
  rows → the **inner** loop parallelises.

```c
for (j = 0; j < 100; j++) {             // serial — depends on column j-1
#pragma omp parallel for
    for (i = 0; i < 100; i++)           // parallel — 100 independent rows
        a[i][j] = f(a[i][j-1]);
}
```

**Exercises 11 and 12 are the key pair.** Identical arithmetic, identical
dependences — but the loop-nest order decides whether the outer or the inner
loop is the parallel one. Placement of the parallel clause follows the
dependence, not the code's appearance.

## Exercise 13 — `printf("a"); printf("b");`

**NO — output dependence on a shared resource.**

Both calls write to `stdout`, which is a single shared object with its own
buffer and its own lock. There is no data dependence on `a` or `b` — the
conflict is with the *device state*. Unordered, the two characters can be
written as `ba`, or interleave part-way inside a buffered flush.

Fixes: serialise with a lock (`#pragma omp critical`), or give each thread its
own buffer and write it once at the end. Note that even `printf` is not
automatically safe just because it looks atomic.

## Exercise 14 — `a = f(x); b = g(x);`

**YES — provided `f` and `g` are pure.**

Both read only `x`; both write different variables. Write–write to distinct
addresses, no read of either result. Independent.

The proviso matters: if `f` modifies `x`, or if `f` and `g` mutate shared state
or produce output, the dependence returns. Parallelising a statement means
parallelising *everything it touches*, including the calls — this is why
compilers need `const`/`pure`/`noexcept`-style information to make the same
decision a human just made.

## Exercise 15 — `for(i=0;i<100;i++) a[i+10] = f(a[i]);`

**NO — loop-carried dependence with distance 10.**

Iteration `k` **reads** `a[k]` and **writes** `a[k+10]`.
Iteration `k+10` **reads** `a[k+10]` — exactly what iteration `k` wrote.

So iteration `k` and iteration `k+10` conflict (RAW across a gap of 10). The
array splits into **10 independent interleaved chains**:

```
0 → 10 → 20 → …      1 → 11 → 21 → …      …      9 → 19 → 29 → …
```

Each chain is internally sequential, but chains do not interact. So the loop is
*not* parallel as written, yet it is not a single serial chain either:

- **Correct as-is:** `collapse` will not help; you need distance-aware
  scheduling.
- **Parallel form:** run the 10 chains concurrently (one per thread), each
  looping `for (k = c; k < 90; k += 10)`, or use a chunked wavefront with a
  barrier every 10 steps.

Misreading this as "distance 1" because the code looks like a shift is the
classic trap: the dependence distance is whatever index gap actually occurs,
here **10**.

## Exercise 16 — `for(i=1;i<100;i++) { a[i]=…; ...=a[i-1]; }`

**NO — loop-carried dependence with distance 1.**

Every iteration writes `a[i]` and the body reads `a[i-1]`, written by iteration
`i-1`. Same shape as Exercise 10: a sequential recurrence along the array,
forcing `i = 1,2,3,…` in order.

Both statements in the body participate: the write of `a[i]` feeds iteration
`i+1`'s read of `a[i]`. Nothing here can be reordered without changing the
result.

## Exercise 17 — `for(i=0;i<100;i++) a[i] = f(a[indexa[i]]);`

**CANNOT BE DECIDED COMPILED-TIME — conservatively NO.**

Iteration `i` reads `a[indexa[i]]`, where `indexa[i]` is an *unknown, data-
dependent* subscript. Two cases:

| Condition on `indexa[]` | Verdict |
|-------------------------|---------|
| every `indexa[i] < i` | raw recurrence → serial (prefix-like) |
| some `indexa[i] == k` for a `k` this loop also writes | conflict → serial |
| all `indexa[i]` point outside `[0,99]`, or to read-only data | independent → parallel |

Iteration `i` writes `a[i]`, so if *any* `indexa[i]` points at a location in
`[0,99]` that is written by another iteration, the iterations conflict; if the
indices happen to point only at untouched memory, they do not.

The deck's own answer (page 77) is the right one:

> *Cannot tell for sure. Parallelization depends on user knowledge of values of
> `indexa[]`. **User can tell, compiler cannot.***

So this is a **programmer assertion**, not an inference: supply
`#pragma omp simd` / `declare simd` / a `restrict`-style guarantee, or insert a
runtime dependence check (inspector-executor) before parallelising. Absent
that assertion, the safe answer is **NO**.

---

## Summary table

| Ex | Code shape | Parallel? | Dependence |
|----|------------|-----------|------------|
| 1 | two scalar stores | **YES** | — |
| 2 | store then load of same var | no | RAW `a` |
| 3 | load then store of same var | no | WAR `a` |
| 4 | two stores to same var | no | WAW `a` |
| 5 | `a[i] = i` | **YES** | — |
| 7 | `a[i]=i; b[i]=2i` per iteration | **YES** | — |
| 8 | two independent loops | **YES** | — |
| 9 | `a[i] += 100` | **YES** | — |
| 10 | `a[i] = f(a[i-1])` | no | RAW, distance 1 (prefix) |
| 11 | row nest, `j` recurrence | **YES** over `i` | inner `j` serial |
| 12 | column nest, `j` recurrence | **YES** over `i` | outer `j` serial |
| 13 | two `printf`s | no | WAW on `stdout` |
| 14 | `a=f(x); b=g(x)` | **YES** | — (if pure) |
| 15 | `a[i+10] = f(a[i])` | no | RAW, distance 10 |
| 16 | `a[i]` uses `a[i-1]` | no | RAW, distance 1 |
| 17 | `a[i] = f(a[indexa[i]])` | unknown → no | data-dependent |

**Counts:** 7 unconditionally parallel (1, 5, 7, 8, 9, 14, plus 11/12 over the
right loop), 8 order-dependent (2, 3, 4, 10, 13, 15, 16), 1 undecidable (17).
Exercise 6 does not appear in the source sheet.
