# Stages G and H — Training the Model on PARAM Rudra

This document records Stage G (training infrastructure) and Stage H
(chained training to completion) of the BDW project: training the
decoder-only Transformer on the cluster with frequent checkpointing,
automatic resume, graceful handling of the SLURM time limit, and a full
200,000-step run assembled out of several separate 15-minute jobs.

Everything below is taken from literal cluster output. Job IDs, numbers and
log lines are quoted verbatim and can be re-checked with the commands shown.

---

## 1. Constraints that shaped the design

The cluster's `training` QOS is the hard constraint for this stage
(verified in Stage A, `ENVIRONMENT_AUDIT.md`):

| Limit | Value | Consequence for training |
|---|---|---|
| `MaxWall` | `00:15:00` | A single job cannot run longer than 15 minutes |
| `MaxTRESPU` | `cpu=4, gres/gpu=1, node=2` | One GPU, four CPUs |
| `MaxSubmitJobs` | `1` | Only one job in the queue at a time |

Because a job is killed after 15 minutes, the training loop **must**:

1. save a checkpoint very frequently (target: every 5–8 minutes),
2. resume automatically from the newest checkpoint on the next submission,
3. survive the time-limit signal instead of losing the run.

Those three requirements drove the whole design below.

---

## 2. SLURM script

`~/bdw-llm/scripts/train.slurm` — all directives, in the order they are
parsed:

```
#SBATCH --job-name=bdw_g_train
#SBATCH --partition=gpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gpus=1
#SBATCH --cpus-per-task=4
#SBATCH --time=00:15:00
#SBATCH --account=tutor
#SBATCH --qos=training
#SBATCH --output=%x-%j.out
#SBATCH --error=%x-%j.err
```

Important detail learned during Stage A: **sbatch stops parsing `#SBATCH`
at the first non-comment, non-blank line.** A bare option line missing its
`#SBATCH` prefix silently drops every directive after it. Every script used
in this project is checked with `bash -n` and its header printed before
submission.

The last line of the script is:

```bash
exec python $HOME/bdw-llm/src/train.py "$@"
```

`exec` matters. See §6.

---

## 3. Training configuration

Verified from the `args { ... }` block printed by every run:

| Setting | Value | Notes |
|---|---|---|
| batch size | 8 | sequences per step |
| sequence length | 1024 | matches Stage E tokenisation |
| tokens per step | 8192 | 8 × 1024 |
| optimizer | AdamW | `betas=(0.9, 0.95)`, `weight_decay=0.1` |
| peak learning rate | `6e-4` | cosine decay to `6e-5` |
| warmup steps | 200 | linear warmup |
| total steps | 200000 | cosine schedule horizon |
| gradient clipping | 1.0 | global norm |
| precision | bfloat16 autocast | forward and backward |
| seed | 1337 | |
| eval interval | 500 steps | |
| log interval | 20 steps | |
| checkpoint interval | 300 s | 5 minutes |
| keep last | 3 checkpoints | older ones rotated out |

Runtime, printed by the job itself:

```
device        : NVIDIA A100 80GB PCIe
torch         : 2.5.1+cu121
params        : 27800576 (27.80 M)
```

Node: `rdgpu01`.

---

## 4. Train / validation split

`load_shards()` reserves the **last** shard as held-out validation so the
evaluated loss is never computed on data the optimiser has seen. The split
is printed by every job:

```
train shards   : 38  rows=37088  tokens=37978112
val shards     : 1  rows=227  tokens=232448  (held out)
```

Training batches come from the 38 training shards with `rng`; evaluation
batches come from the single validation shard with a separate
`val_rng = random.Random(seed + 991)`, so evaluation can never consume a
training batch.

Arithmetic check: `37,978,112 + 232,448 = 38,210,560`, which equals
`37,315 rows × 1024`. Stage E counted 38,210,943 raw tokens, so
`38,210,943 - 38,210,560 = 383` trailing tokens (0.001%) were dropped when
the stream was packed into whole 1024-token rows.

**Limitation (stated openly):** the held-out set is small — 232,448 tokens,
0.61% of the corpus — because the final shard happens to contain only 227
rows. Val-loss numbers are therefore somewhat noisy, and Stage I performs a
wider evaluation rather than relying on this thin split.

---

## 5. Checkpointing

Design:

- save every **300 seconds** (5 minutes), inside the 5–8 minute target,
- keep the newest **3** checkpoints, rotate out the rest,
- write via `path + ".tmp"` then `os.replace()` so an interrupted write can
  never corrupt a good checkpoint,
- write a small human-readable `*.pt.meta` sidecar next to each `*.pt`,
- rotation removes **both** the `.pt` and its `.meta`.

Observed behaviour — two saves exactly 300 s apart during the first run:

```
[ckpt] saved step_0014583.pt  (wall 300s, step 14583, lr 5.93e-04)
[ckpt] saved step_0029208.pt  (wall 300s, step 29208, lr 5.72e-04)
```

Example sidecar, produced by the final-save path:

```json
{
  "step": 35038,
  "tokens_seen": 287031296,
  "saved_at": "2026-10-16T14:51:41",
  "loss": 3.8946850299835205,
  "lr": 0.0005604963091935635,
  "wall_s": 22.70467519760132
}
```

Rotation evidence (`step_0014583.pt` and later `step_0029208.pt` removed
together with their sidecars):

```
[ckpt] rotated out step_0014583.pt
[ckpt] rotated out step_0029208.pt
```

On-disk footprint after Stage G: `955M` in `checkpoints/`, `292M` in
`tokens/`, `165M` in `data/` (home quota has ~1.6 T free).

---

## 6. Auto-resume — proof

On startup `train.py` calls `find_latest_ckpt()`, which globs
`checkpoints/step_*.pt` and takes the newest. Job **31831** was submitted
with `--max-steps 60` purely to prove this path. Verbatim log:

```
[resume] loading /home/tutor/3ioip3lt/bdw-llm/checkpoints/step_0029208.pt
[resume] step=29208 tokens_seen=239271936 last_loss=4.3126
...
[max-steps] reached 60 this run

[final] saved step_0029268.pt
...
steps total     : 29268
steps this run  : 60
TRAIN_DONE
```

The model stepped **29208 → 29268**, i.e. exactly 60 steps, and wrote a new
checkpoint. Optimizer state and `tokens_seen` came back from disk, not from
zero. Job state: `COMPLETED`, elapsed `00:00:36`.

All resumes observed across Stage G:

```
[resume] step=29208 tokens_seen=239271936 last_loss=4.3126
[resume] step=29268 tokens_seen=239763456 last_loss=4.2795
[resume] step=34038 tokens_seen=278839296 last_loss=4.3325
```

---

## 7. Surviving the time limit — proof

SLURM sends `SIGTERM` when a job reaches its wall time. `train.py` installs
a handler for `SIGTERM`/`SIGUSR1` that sets a stop flag; the loop then
saves a checkpoint, prints a summary and exits.

Job **31833** was deliberately submitted with `-t 00:02:00` so the signal
was guaranteed to arrive. Verbatim log tail:

```
[signal] 15 received -> will checkpoint and stop
[ckpt] rotated out step_0014583.pt
[ckpt] saved step_0034038.pt  (wall 103s, step 34038, lr 5.63e-04)

[final] saved step_0034038.pt

=== summary ===
steps total     : 34038
tokens seen     : 278839296 (7.30 epochs)
stop reason     : signal
TRAIN_DONE
```

`sacct` reported the step as `TIMEOUT` / `00:02:06` while the batch process
finished `COMPLETED` — the job hit its limit, but the training process shut
itself down cleanly and lost nothing since the previous 5-minute checkpoint.

**Why `exec` was necessary.** The first run (job 31814) used a plain
`python ...` child of the batch shell. It produced **no** `[signal]` line
and its batch process ended `CANCELLED`:

```
31814       | bdw_g_train | TIMEOUT  | 00:15:14 | 4
31814.batch | batch       | CANCELLED| 00:15:15 | 4
31833       | bdw_g_train | TIMEOUT  | 00:02:06 | 4
31833.batch | batch       | COMPLETED| 00:02:08 | 4
```

With `exec python ...` the interpreter *is* the batch process, so the
signal reaches the handler directly — job 31833 shows both the handler
firing and a `COMPLETED` batch process. Job 31814 still retained its state
only because the 5-minute periodic checkpoint had already fired twice.

---

## 8. Jobs run in this stage

Stage G verification jobs:

| Job | Purpose | `sacct` state | Elapsed | Outcome |
|---|---|---|---|---|
| 31814 | first full training run | `TIMEOUT` (batch `CANCELLED`) | `00:15:14` | 43,560 steps; checkpoints at 14,583 and 29,208 |
| 31831 | auto-resume proof (`--max-steps 60`) | `COMPLETED` | `00:00:36` | resumed 29,208 → 29,268 |
| 31833 | time-limit signal proof (`-t 00:02:00`) | `TIMEOUT` (batch `COMPLETED`) | `00:02:06` | resumed 29,268 → 34,038, graceful save |
| 31836 | held-out split proof (`--max-steps 1000`) | `COMPLETED` | `00:00:58` | resumed 34,038 → 35,038; first `val_loss` |

Stage H chained training jobs — the same script, submitted again and again,
each one resuming where the previous was killed:

| Job | Role | State | Elapsed | Resume in | Step out |
|---|---|---|---|---|---|
| 31844 | round 1 | `TIMEOUT` (batch `COMPLETED`) | `00:15:18` | 35,038 | 76,269 |
| 31859 | round 2 | `TIMEOUT` (batch `COMPLETED`) | `00:15:15` | 76,269 | 117,602 |
| 31863 | round 3 | `TIMEOUT` (batch `COMPLETED`) | `00:15:13` | 117,602 | 159,084 |
| 31866 | round 4 | `TIMEOUT` (batch `COMPLETED`) | `00:15:02` | 159,084 | 199,496 |
| 31870 | final 504 steps (`--max-steps 504`) | **`COMPLETED`** | `00:00:47` | 199,496 | **200,000** |

Stage I evaluation jobs (documented in `EVALUATION.md`): **31862**
(`COMPLETED`, `00:00:29`, step 117,602) and **31871** (`COMPLETED`,
`00:00:18`, step 200,000).

### The chain, step by step

Eight auto-resumes were observed in total, each one continuing the previous
job's optimizer state:

```
[resume] step=29208  tokens_seen=239271936  last_loss=4.3126
[resume] step=29268  tokens_seen=239763456  last_loss=4.2795
[resume] step=34038  tokens_seen=278839296  last_loss=4.3325
[resume] step=35038  tokens_seen=287031296  last_loss=3.8947
[resume] step=76269  tokens_seen=624795648  last_loss=3.8867
[resume] step=117602 tokens_seen=963395584  last_loss=3.9574
[resume] step=159084 tokens_seen=1303216128 last_loss=3.8624
[resume] step=199496 tokens_seen=1634271232 last_loss=3.5075
```

Fifteen checkpoints were written across those runs, every periodic one at
`wall 300s` or at the signal:

```
[ckpt] saved step_0014583.pt  (wall 300s, ...)   [ckpt] saved step_0131558.pt  (wall 300s, ...)
[ckpt] saved step_0029208.pt  (wall 300s, ...)   [ckpt] saved step_0145532.pt  (wall 300s, ...)
[ckpt] saved step_0034038.pt  (wall 103s, ...)   [ckpt] saved step_0159084.pt  (wall 291s, ...)
[ckpt] saved step_0048914.pt  (wall 300s, ...)   [ckpt] saved step_0172981.pt  (wall 300s, ...)
[ckpt] saved step_0062880.pt  (wall 300s, ...)   [ckpt] saved step_0186957.pt  (wall 300s, ...)
[ckpt] saved step_0076269.pt  (wall 287s, ...)   [ckpt] saved step_0199496.pt  (wall 269s, ...)
[ckpt] saved step_0090236.pt  (wall 300s, ...)
[ckpt] saved step_0104214.pt  (wall 300s, ...)   [final] saved step_0200000.pt
[ckpt] saved step_0117602.pt  (wall 288s, ...)
```

**Maximum work lost to a wall kill was one checkpoint interval — 5 minutes.**
Every one of the five `TIMEOUT` jobs ended with the batch process
`COMPLETED` and a summary block, i.e. no job was ever lost abruptly after
the `exec python` fix in §7.

### Final run

```
[resume] step=199496 tokens_seen=1634271232 last_loss=3.5075
[final] saved step_0200000.pt
steps total     : 200000
tokens seen     : 1638400000 (43.14 epochs)
loss first      : 3.7801
loss last       : 3.5953
loss decreased  : True
stop reason     : total-steps
TRAIN_DONE
```

`sacct`: `31870|COMPLETED|0:0|00:00:47`. The learning-rate schedule
finished exactly at floor — the final checkpoint records
`"lr": 6.000000003337662e-05`, i.e. `min_lr = 6e-5`.

Throughput was stable throughout at **~383,000 tokens/s** (≈ 47 steps/s),
which is why each 15-minute window delivered about 41,500 steps.

---

## 9. Results — did the loss go down?

Yes. Two different measurement methods were used, so they are reported
separately rather than merged into one curve.

**Initial training (job 31814).** Loss falls steeply from random
initialisation. First log lines:

```
20       8.8756       6.00e-05   131558     0m01s     0.4
40       8.1335       1.20e-04    97852     0m01s     0.9
60       7.4422       1.80e-04    77984     0m02s     1.3
```

From `logs/train_metrics.jsonl` (99 entries):

| step | `eval_loss` |
|---|---|
| 500 | 6.0632 |
| 1000 | 5.8707 |
| 2000 | 5.3826 |
| 5000 | 4.7569 |
| 10000 | 4.4149 |
| 20000 | 4.0433 |
| 43500 | 4.1224 |

Entries at step ≤ 34000 were produced **before** the held-out split existed
and were measured on the training stream, so they are optimistic and are
shown only to demonstrate the downward trend from 6.06 to about 4.1.

**Held-out validation (job 31836, after the split was introduced):**

```
[eval] step 34500  val_loss=3.7134  (train-window 4.1936)
[eval] step 35000  val_loss=3.8597  (train-window 4.1861)
```

`val_loss` sits below `train-window`, which is expected: dropout is active
while computing training loss but disabled during evaluation.

Job 31836's own summary confirms the decrease on a like-for-like basis:

```
loss first      : 4.1349
loss last       : 3.8947
loss tail mean  : 4.1802
loss decreased  : True
stop reason     : total-steps
TRAIN_DONE
```

**Throughput** stabilises at roughly **385,000 tokens/second**
(e.g. `384717` at step 30,000), about 47 steps/s.

**Observed plateau.** From roughly step 15,000 onward the loss hovers near
4.0–4.2 (train) / 3.7–3.9 (held-out) while the model at that point was
still only 7.6 epochs into the corpus. This is consistent with a 27.8 M
parameter model running out of capacity, not with a training bug.

**Full run to 200,000 steps (Stage H).** The chained jobs continued the
same trend through the cosine decay:

| Step | `train_loss` (trailing) | `eval_loss` | `lr` |
|---|---|---|---|
| 198500 | 3.7611 | 3.8951 | 6.008e-05 |
| 199000 | 3.8390 | 3.9581 | 6.003e-05 |
| 199500 | 3.7645 | 3.9494 | 6.001e-05 |
| **200000** | **3.5953** | **4.0082** | **6.000e-05** |

`logs/train_metrics.jsonl` holds **429** entries in total.

Note the two evaluation methods part company here, which is exactly why
they are not merged:

* in-training `eval_loss` on the thin held-out shard: **4.0082**
  (ppl ≈ 55.0) at step 200,000;
* truly unseen, URL-disjoint corpus in Stage I: **NLL 3.9589**
  (ppl **52.40**).

The shard used by the in-training split is only 232,448 tokens and was
thoroughly memorised during steps 0–34,038 (before the split existed), so
neither number should be treated as the final word — Stage I's `EVALUATION.md`
is the authoritative generalisation measurement.

**Learning rate reached its floor exactly** when training stopped:
`"lr": 6.000000003337662e-05` in `step_0200000.pt.meta`, with
`tokens_seen = 1,638,400,000 = 200,000 × 8192` (43.14 epochs).

**Generation** was first checked at this point: greedy decoding produces
fluent but repetitive text, sampling at `t=0.8, k=50` produces coherent
sentences. Full samples and commentary are in `EVALUATION.md`.

---

## 10. Bugs found and fixed during this stage

Recorded honestly because each one was visible in real output:

1. **Throughput printed nonsense.** `tok/s` divided interval tokens by
   *cumulative* elapsed time, so it displayed `183` instead of ~385,000.
   Fixed by timing the interval between log lines.
2. **`(train-window …)` printed nonsense.** An unreset cumulative sum was
   divided by `log_interval`, giving values such as `9706.0012` while the
   real loss was ~4.1. Replaced with a trailing 200-loss mean; now prints
   `4.1936`.
3. **Final save wrote no `.meta` sidecar**, so `step_0029268.pt` has no
   sidecar while every periodic checkpoint does. Moved sidecar writing into
   `save_ckpt()` so both paths produce one.
4. **Rotation orphaned `.meta` files.** `rotate_ckpts()` deleted only the
   `.pt`. Now removes the sidecar too — verified: `step_0014583.pt.meta`
   disappeared together with its checkpoint.
5. **Graceful shutdown never fired** in job 31814 because the batch script
   ran `python` as a child of `bash`. Fixed with `exec python` (§7).
6. **Driver bug:** `sbatch --max-steps 60 train.slurm` passed the option to
   `sbatch`, not to the script (`sbatch: unrecognized option`). Script
   arguments must follow the script name: `sbatch train.slurm --max-steps 60`.
7. **`stop reason` always claimed `total-steps`.** The summary line was
   computed as `signal if _stop_requested else total-steps`, but a job killed
   by the `MaxWall` limit never reached that line at all (fixed by
   `exec python`, §7), so for five chained jobs the printed reason was
   simply never re-examined. After the fix it *was* visible, and the label
   was wrong for any job that stopped for another reason. Replaced with an
   explicit `stop_reason` of `signal` / `total-steps` / `max-steps` /
   `loop-exit`. Verified live in job 31870: `stop reason : total-steps`.
8. **Duplicate final save.** The `--max-steps` path and the end-of-loop
   save both wrote the final checkpoint. A `last_saved_step` guard now
   prevents the second write, verified by the log line
   `[final] step 76269 already saved during this run`.

---

## 11. Artifacts

| Path | Description | md5 |
|---|---|---|
| `~/bdw-llm/src/train.py` | training loop | `eb012c3eb69822974a32e3ea0845f259` |
| `~/bdw-llm/scripts/train.slurm` | SLURM script (`exec python … "$@"`) | `3e2ec27a1e12ad04efb121964c7883d1` |
| `~/bdw-llm/scripts/bdw_g_train-<job>.out` | per-job log (11 training jobs) | — |
| `~/bdw-llm/checkpoints/step_<N>.pt` (+ `.meta`) | model, optimizer, RNG state | — |
| `~/bdw-llm/logs/train_metrics.jsonl` | per-eval metrics (429 rows) | — |

Checkpoints on disk at the end of Stage H — the three newest, each with a
`.meta` sidecar:

```
-rw-rw-r-- 176  16:11  step_0200000.pt.meta
-rw-rw-r-- 176  16:11  step_0200000.pt      333675250
-rw-rw-r-- 178  16:08  step_0199496.pt.meta
-rw-rw-r-- 178  16:08  step_0199496.pt      333675250
-rw-rw-r-- 178  16:03  step_0186957.pt.meta
-rw-rw-r-- 178  16:03  step_0186957.pt      333675250
```

**Final checkpoint: `step_0200000.pt`** (step 200,000, loss 3.5953,
lr 6.00e-05, 333,675,250 bytes).

`du -sh ~/bdw-llm/*`: checkpoints 955 M, tokens 292 M, data 186 M,
venv 5.7 G — about 7.2 GB total, with `/home` at 94% of 25 T (1.6 T free).

---

## 12. Honest limitations

- **200,000 steps were reached, but not without over-fitting.** Training
  processed 1.638 B tokens against a 38.0 M-token training split —
  **43 epochs** of the same 165 MB. Stage I measures the cost: the
  generalisation gap grew from 0.286 nats (step 117,602) to 0.395 nats
  (step 200,000). More epochs bought a 10% perplexity improvement and
  simultaneously more memorisation.
- The in-training held-out shard is thin (232,448 tokens, 0.61%) and was
  in the training stream for the first 34,038 steps, so its `val_loss` is
  not a clean generalisation signal. `EVALUATION.md` replaces it.
- Metrics written to `train_metrics.jsonl` before step 34,500 used the
  training stream for evaluation and must not be compared with later rows.
- Wall time forced 5 chained jobs plus 1 finishing job; no single job ever
  ran the full schedule, so the loss curve is stitched from separate
  processes. Resume correctness is proven (§6), but gradient-noise
  statistics differ from a single uninterrupted run.
- Every training job shared one QOS (`training`, 15 min, 1 GPU), so no
  multi-GPU, distributed or mixed-precision comparison was attempted.
