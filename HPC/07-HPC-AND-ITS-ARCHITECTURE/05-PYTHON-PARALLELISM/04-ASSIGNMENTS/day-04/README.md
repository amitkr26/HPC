# Day 04 — Distributed Python Computing (Assignment Solutions)

Four exercises from `python_parallel_day4_assignment.pdf`:
SCOOP, Pyro4, RPyC and Celery.

## Files

| File | Exercise | Needs |
|------|----------|-------|
| `ex01_scoop_monte_carlo.py` | 1 — Monte-Carlo integration with SCOOP | `scoop` |
| `banking_server.py` | 2A — Pyro4 remote banking server | `Pyro4` |
| `banking_client.py` | 2B — Pyro4 interactive CLI client | `Pyro4` (server running) |
| `inspector_server.py` | 3A — RPyC system inspector server | `rpyc` |
| `inspector_client.py` | 3B — RPyC interactive CLI client | `rpyc` (server running) |
| `celery_config.py` | 4 — Celery app configuration | `celery` + broker |
| `tasks.py` | 4 — Celery task definitions | `celery` + broker |
| `order_client.py` | 4 — independent tasks + chained pipeline | `celery` + broker + worker |

## Prerequisites

```bash
pip install scoop Pyro4 rpyc celery
# Celery only: a broker + result backend, e.g.
docker run -d -p 6379:6379 redis:alpine
```

These packages are **not** installed on this Windows machine — the scripts were
syntax-checked here but must be executed on the course cluster.

## Exercise 1 — SCOOP (`ex01_scoop_monte_carlo.py`)

```bash
python -m scoop ex01_scoop_monte_carlo.py              # 10,000,000 evals / 16 chunks
python -m scoop ex01_scoop_monte_carlo.py 1000000 8    # smaller/faster run
python ex01_scoop_monte_carlo.py 1000000 8             # single-process fallback
```

The script splits the workload into 16 chunks, runs them with
`scoop.futures.map()`, prints the estimated integral of `sin(x)*exp(-x)` on
`[0, pi]` against the analytic value, then replays the same chunks sequentially
in a `for` loop and prints the speed-up. Optional CLI args: `[total_samples] [num_chunks]`.
For a multi-machine run add `--hostfile hosts.txt` to the scoop runner.

## Exercise 2 — Pyro4 (`banking_server.py` + `banking_client.py`)

```bash
pyro-ns                                                    # optional name server
python banking_server.py                                   # prints the PYRO:... URI
python banking_client.py                                   # paste the URI (empty input
                                                           # falls back to PYRONAME:BankService)
```

Menu: balance / deposit / withdraw / statement / exit.
Server returns a **float** (new balance) on success and an **error string** on
validation or insufficient-funds failures; the client branches on that type.
The client exits cleanly on EOF, Ctrl+C, invalid choices and
`Pyro4.errors.CommunicationError` / `NamingError`.

## Exercise 3 — RPyC (`inspector_server.py` + `inspector_client.py`)

```bash
python inspector_server.py                                 # port 18861
python inspector_client.py                                 # or: python inspector_client.py localhost 18861
```

Menu: system dashboard / list remote files / power table / safe expression
evaluation / disconnect. Expressions are parsed with `ast` and only a
whitelisted subset (numeric literals, arithmetic/bitwise operators, `math.*`
names and calls) is evaluated — no `eval()` of arbitrary code.
Missing directories and bad expressions are reported as errors instead of
crashing the menu loop.

## Exercise 4 — Celery (`celery_config.py` + `tasks.py` + `order_client.py`)

```bash
docker run -d -p 6379:6379 redis:alpine                   # broker + backend
celery -A tasks worker --loglevel=info                    # terminal 1 (as per spec hint)
python order_client.py                                    # terminal 2
```

`celery_config.py` creates the `order_system` app (Redis broker `db 0`,
backend `db 1`, `include=["tasks"]`); `celery -A celery_config worker` works
too. The client prints each task UUID, polls status with progress dots, then
runs the `validate_order | calculate_tax_and_discount | generate_invoice_pdf`
chain and prints the final invoice message. Broker outages, worker-less
time-outs and Ctrl+C are handled without a traceback.

## Notes / deliberate deviations

- **Exercise 1**: `scoop.futures.map()` is fed through a module-level
  `evaluate_chunk(task)` adapter because the tasks are `(id, samples)` pairs —
  keeps the required `evaluate_subrange(subrange_id, samples_count)` signature
  and gives a single-iterable `map()` call. Optional CLI args were added for
  quick test runs; defaults are the spec's 10,000,000 / 16.
- **Exercise 2**: the server also registers `PYRONAME:BankService` when a Pyro
  name server is running (spec only requires printing the URI); an empty URI
  at the client prompt falls back to that name. `deposit()`/`withdraw()`
  return the new balance (float) or an error string, as implied by the spec's
  "return error string if insufficient funds".
- **Exercise 3**: `exposed_execute_expression` uses a whitelisted AST walker
  instead of bare `eval()` because the spec asks for a *safe* evaluation;
  `max_exponent` is capped at 512 and integer powers at `2**4096` so a client
  cannot hang the server. Client accepts optional `[host] [port]` arguments.
- **Exercise 4**: `celery_config.py` adds `include=["tasks"]` (and JSON
  serializer settings) on top of the spec snippet so both
  `celery -A tasks worker` and `celery -A celery_config worker` work;
  `validate_order` returns `status: "REJECTED"` plus an `error` key for
  invalid input instead of raising, so a client can still print the result.
- Multiprocessing/daemon code in every file is guarded by
  `if __name__ == "__main__":`, and both CLI menu apps terminate on EOF.
