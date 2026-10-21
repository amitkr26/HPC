# Instruction Fine-tuning — Stage L

**Executed:** 2026-10-21 10:12–10:19 IST
**Where:** compute node `rdgpu01` (A100 80GB), `--partition=gpu --gpus=1 --cpus-per-task=4 --time=00:15:00 --account=tutor --qos=training`
**Scripts:** `src/finetune.py`, `scripts/finetune.slurm`
**Output:** `~/bdw-llm/checkpoints_ft/`

Loads the 200k-step pre-trained model and fine-tunes it on the Stage K
instruction shards, reusing the Stage G auto-resume / wall-clock checkpoint /
SIGTERM-save machinery so the 15-minute MaxWall limit is survivable.

---

## 1. What is deliberately different from pre-training

| | Stage G/H (pre-train) | Stage L (fine-tune) |
|---|---|---|
| Starting weights | random init | `checkpoints/step_0200000.pt` |
| Architecture | hardcoded constructor | taken from the checkpoint's own `model_config` |
| Checkpoint dir | `checkpoints/` | **`checkpoints_ft/`** |
| Optimizer | fresh AdamW | fresh AdamW (base optimizer state **not** inherited) |
| Step counter | starts 0 | restarts 0 |
| Peak LR | `6e-4` | `3e-5` |
| Schedule | cosine to `6e-5` over 200k steps | cosine to `3e-6` over 3k steps |
| Warmup | 200 | 100 |
| Data | `tokens/shards/` (38.2 M tokens) | `data/instruct_tokens/shards/` (2.93 M tokens) |
| Wall-clock checkpoint | every 300 s | every 300 s (unchanged) |
| SIGTERM save | yes | yes (unchanged) |

Two points worth spelling out:

* **Separate checkpoint directory.** Fine-tuning writes to `checkpoints_ft/`.
  `src/finetune.py` hard-refuses a `--ckpt-dir` that resolves to the
  pre-training directory, so `step_0200000.pt` can never be overwritten. This
  was verified live: the base file is still 333,675,250 bytes, still dated
  Oct 16 16:11, still md5 `bd4772448505442086d4557d32950e84`.
* **Fresh optimizer, not inherited.** The base checkpoint does contain AdamW
  state, but carrying it forward would be wrong: the loss landscape and the
  data distribution have both changed, and the pre-training cosine schedule
  was tuned for a 200k-step horizon ending at LR 6e-5. We restart at step 0
  with a short warmup and a 10× lower peak LR.

The architecture is read from `blob["model_config"]` rather than hardcoded, so
the fine-tuned model is structurally guaranteed to match the base. The run log
confirms this: `vocab=16384 seq_len=1024 d_model=512 layers=6 heads=8 d_ff=2048`,
`params 27,800,576` — identical to Stage F.

## 2. Schedule

3000 steps at batch 8 × seq 1024 = **24,576,000 tokens ≈ 12.3 epochs** over
1,998,848 training tokens. The whole thing finishes in about a minute of GPU
time, so it fits inside a single 15-minute wall with enormous headroom — the
chaining machinery is a safety net here, not a necessity. It is still
implemented and was proven to work (§4).

| | rows | tokens | role |
|---|---|---|---|
| `shard_0000.npy` | 976 | 999,424 | train |
| `shard_0001.npy` | 976 | 999,424 | train |
| `shard_0002.npy` | 906 | 927,744 | **held out** |

The held-out shard was designated in Stage K and never touched during
optimisation.

## 3. Jobs

| Job | State | Elapsed | What it did |
|---|---|---|---|
| 32099 | COMPLETED | 00:00:33 | `--max-steps 300` — load base, save first checkpoint |
| 32100 | COMPLETED | 00:01:19 | **auto-resumed** from step 300, ran to 3000, `stop reason: total-steps` |
| 32101 | TIMEOUT | 00:02:13 | isolated wall-test — SIGTERM → checkpoint → `stop reason: signal` |
| 32102 | COMPLETED | — | `--eval-only` on the **base** model |
| 32103 | COMPLETED | — | `--eval-only` on fine-tuned step 3000 |
| 32104 | COMPLETED | — | `--eval-only` on fine-tuned step 300 |

### Job 32099 — base load

```
train shards   : 2  rows=1952  tokens=1998848
val shards     : 1  rows=906  tokens=927744  (held out)
[base] loading pre-training weights from /home/tutor/3ioip3lt/bdw-llm/checkpoints/step_0200000.pt
[base] architecture: vocab=16384 seq_len=1024 d_model=512 layers=6 heads=8 d_ff=2048
[base] pre-training provenance: step=200000 tokens_seen=1638400000 saved_at=2026-10-16T16:11:09
[base] fresh optimizer + step 0 (not inheriting pre-training optimizer state or its 200k-step schedule)
params        : 27800576 (27.80 M)
[eval] step 100  val_loss=3.6398  val_ppl=38.09  (train-window 3.9075)
[eval] step 200  val_loss=3.5719  val_ppl=35.59  (train-window 3.7579)
[eval] step 300  val_loss=3.3775  val_ppl=29.30  (train-window 3.5548)
[max-steps] reached 300 this run
[final] saved step_0000300.pt
steps total     : 300
tokens seen     : 2457600 (1.23 epochs)
loss first      : 4.3042
loss last       : 3.4510
loss decreased  : True
final held-out  : val_loss=3.4421 val_ppl=31.25
stop reason     : max-steps
FINETUNE_DONE
```

### Job 32100 — auto-resume, full run

```
[resume] loading fine-tune checkpoint /home/tutor/3ioip3lt/bdw-llm/checkpoints_ft/step_0000300.pt
[resume] step=300 tokens_seen=2457600 last_loss=3.4510
[final] saved step_0003000.pt
steps total     : 3000
loss first      : 3.7934
loss last       : 2.8978
loss decreased  : True
final held-out  : val_loss=3.3238 val_ppl=27.76
stop reason     : total-steps
FINETUNE_DONE
```

### Job 32101 — MaxWall survival (isolated dir)

Submitted with `sbatch -t 00:02:00 --total-steps 20000 --ckpt-dir
checkpoints_ft_walltest` so the real fine-tune checkpoint could not be touched:

```
[signal] 15 received -> will checkpoint and stop
[ckpt] saved step_0005510.pt  (wall 114s, step 5510, lr 2.54e-05)
[final] step 5510 already saved during this run
steps total     : 5510
loss first      : 4.3042
loss last       : 2.6533
loss decreased  : True
final held-out  : val_loss=3.3652 val_ppl=28.94
stop reason     : signal
FINETUNE_DONE
```

Slurm sent SIGTERM, the handler wrote `step_0005510.pt` **before** the kill,
and the job then exited `TIMEOUT`. This is the same code path Stage G job
31833 proved during pre-training. The isolated directory was deleted
afterwards and `checkpoints_ft/` still contains exactly `step_0000300` and
`step_0003000`.

## 4. Held-out curve

`logs/finetune_metrics.jsonl`, real run only (the isolated job 32101 also
appends to this file and is identifiable by its much higher LR — it was
running a 20k-step cosine):

| step | held-out loss | | step | held-out loss |
|---|---|---|---|---|
| 100 | 3.6398 | | 1600 | 3.3712 |
| 200 | 3.5719 | | 1700 | 3.3444 |
| 300 | 3.3775 | | 1800 | 3.3277 |
| 400 | 3.4778 | | 1900 | 3.3323 |
| 500 | 3.4930 | | 2000 | 3.2755 |
| 600 | 3.3277 | | 2100 | 3.3223 |
| 700 | 3.4186 | | **2200** | **3.2323 (best)** |
| 800 | 3.3807 | | 2300 | 3.2815 |
| 900 | 3.2768 | | 2400 | 3.2379 |
| 1000 | 3.3500 | | 2500 | 3.2890 |
| 1100 | 3.4908 | | 2600 | 3.2738 |
| 1200 | 3.2837 | | 2700 | 3.2652 |
| 1300 | 3.3296 | | 2800 | 3.3287 |
| 1400 | 3.3032 | | 2900 | 3.2562 |
| 1500 | 3.3782 | | 3000 | 3.3883 |

Best held-out point is **step 2200 at 3.2323**. The curve is noisy because
each point is only 4 batches × 8 sequences, and the run is short enough that
12 epochs over 2 M tokens is near the edge of overfitting — train loss keeps
falling (4.30 → 2.90) while held-out plateaus around 3.23–3.39. Step 3000 was
kept as the shipped checkpoint because the schedule had fully decayed there
and its independent re-evaluation (§5) is within noise of the best point.

## 5. Did fine-tuning actually help?

Each checkpoint was scored on the held-out shard with a dedicated
`--eval-only` run (16 rounds of batch 8 = 128 batches, far more stable than
the 4-round in-loop eval):

| Model | Held-out loss | Held-out ppl | vs base |
|---|---|---|---|
| **Base** (pre-trained, step 200,000) | 4.0632 | 58.16 | — |
| Fine-tuned step 300 | 3.4754 | 32.31 | 0.5878 better |
| **Fine-tuned step 3000 (shipped)** | **3.3315** | **27.98** | **0.7317 better (2.08×)** |

So instruction fine-tuning cuts held-out perplexity on conversational text
from 58.16 to 27.98. Note this is a *different* held-out set from Stage I's
unseen web-prose corpus (which measured 52.40) — 4.06 nats here is the base
model's loss on dolly-style text specifically, and 3.33 is where it lands
after fine-tuning.

## 6. Artefacts

| File | Size | md5 |
|---|---|---|
| `src/finetune.py` | 17,368 B | `32f9377366cc30a3b54ac9a92c7a5f9d` |
| `scripts/finetune.slurm` | 823 B | `4e00fa9f3c1bf9269d167c749a6e673d` |
| `checkpoints_ft/step_0000300.pt` | 333,674,866 B | `9c9f39a82a2d673af4a3627010579d16` |
| `checkpoints_ft/step_0003000.pt` | 333,675,442 B | `7cdfcc94ef0ac7ccae7670e726dcbe5f` |
| `logs/finetune_metrics.jsonl` | — | `ba90680f6efd734e815993f7ae0e0277` |
| `checkpoints/step_0200000.pt` (base, **unchanged**) | 333,675,250 B | `bd4772448505442086d4557d32950e84` |

All `.err` files for the six Stage L jobs were empty.

## 7. Next step

Stage M runs chat with retrieval on the **login node** (the compute nodes have
no DNS): DuckDuckGo / Wikipedia for the top-2 passages, then CPU inference
with `checkpoints_ft/step_0003000.pt` — 27.8 M parameters fits comfortably in
host RAM.

_Generated from Stage L job output; evidence re-read from the cluster._
