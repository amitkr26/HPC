"""Exercise 1 - JSON Configuration Manager.

Manages a parallel-computing job configuration using JSON serialization:
define, save, load, modify, re-save, and pretty-print the configuration.
"""

import json


def save_config(config, path):
    """Write ``config`` to ``path`` as pretty-printed JSON."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)
    print(f"Saved configuration to {path}")


def load_config(path):
    """Load and return the configuration dictionary stored at ``path``."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"ERROR: configuration file {path} not found.")
        raise
    except json.JSONDecodeError as exc:
        print(f"ERROR: {path} is not valid JSON: {exc}")
        raise


def pretty_print(config, heading):
    """Pretty-print ``config`` under ``heading``."""
    print(f"\n--- {heading} ---")
    print(json.dumps(config, indent=4))


def main():
    """Run the full save / load / modify / verify cycle."""
    config = {
        "job_name": "matrix_benchmark",
        "num_workers": 4,
        "chunk_size": 1000,
        "timeout_sec": 30.0,
        "retry_on_failure": True,
        "input_files": ["data_part1.csv", "data_part2.csv",
                        "data_part3.csv"],
        "output_dir": "/results/run_001",
        "parameters": {
            "algorithm": "strassen",
            "precision": "double"
        }
    }

    path = "job_config.json"
    save_config(config, path)

    loaded = load_config(path)
    pretty_print(loaded, "Configuration loaded back from disk")

    print("\nModifying num_workers: 4 -> 8")
    loaded["num_workers"] = 8
    save_config(loaded, path)

    final = load_config(path)
    pretty_print(final, "Final configuration (read from disk)")

    print("\nVerification:")
    print(f"  num_workers on disk = {final['num_workers']}")
    print(f"  matches in-memory value: {final['num_workers'] == loaded['num_workers']}")
    print(f"  keys preserved: {list(final.keys()) == list(config.keys())}")


if __name__ == "__main__":
    main()
