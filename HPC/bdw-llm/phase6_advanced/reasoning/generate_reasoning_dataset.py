#!/usr/bin/env python3
"""Generate deterministic Phase 6 reasoning SFT data with <think> traces."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DEFAULT_TOKENIZER = ROOT / "merged" / "bdw-7b-sft"
DEFAULT_OUT = HERE / "data"
SYSTEM_PROMPT = (
    "You are a careful reasoning assistant. Work through the problem step by "
    "step inside a <think>...</think> block, then give a concise final answer "
    "after the closing tag. Do not omit the closing tag."
)
TRAIN_PER_CATEGORY = 40
EVAL_PER_CATEGORY = 8
CATEGORIES = ("math", "logic", "coding")
NAMES = [
    "Ada", "Ben", "Cara", "Dev", "Elena", "Farid", "Grace", "Hugo",
    "Iris", "Jonah", "Kira", "Leo", "Maya", "Nico", "Omar", "Priya",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def format_target(steps: list[str], final: str) -> str:
    numbered = "\n".join(f"{index}. {step}" for index, step in enumerate(steps, 1))
    return f"<think>\n{numbered}\n</think>\n\n{final}"


def make_example(
    category: str,
    difficulty: str,
    question: str,
    steps: list[str],
    final: str,
    kind: str,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "kind": kind,
        "reasoning_steps": steps,
        "answer": final,
    }
    if extra:
        metadata.update(extra)
    return {
        "category": category,
        "difficulty": difficulty,
        "question": question,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question},
            {"role": "assistant", "content": format_target(steps, final)},
        ],
        "metadata": metadata,
    }


def math_inventory(rng: random.Random) -> dict[str, Any]:
    crates = rng.randint(8, 40)
    per_crate = rng.randint(6, 30)
    total = crates * per_crate
    shipped = rng.randint(20, max(21, total // 2))
    received = rng.randint(5, 50)
    remaining = total - shipped + received
    question = (
        f"A warehouse has {crates} crates. Each crate holds {per_crate} bottles. "
        f"The warehouse ships {shipped} bottles and then receives {received} new "
        "bottles. How many bottles are in the warehouse now?"
    )
    steps = [
        f"{crates} crates with {per_crate} bottles each contain "
        f"{crates} x {per_crate} = {total} bottles.",
        f"After shipping {shipped} bottles, {total} - {shipped} = "
        f"{total - shipped} bottles remain.",
        f"After receiving {received} more, {total - shipped} + {received} = "
        f"{remaining} bottles remain.",
    ]
    return make_example(
        "math", "easy", question, steps, f"{remaining} bottles",
        "inventory",
    )


def math_discount(rng: random.Random) -> dict[str, Any]:
    price = rng.choice([80, 100, 120, 160, 200, 240, 300, 360])
    percent = rng.choice([10, 15, 20, 25, 30, 40])
    discount = price * percent // 100
    shipping = rng.randint(3, 15)
    final = price - discount + shipping
    question = (
        f"A jacket costs ${price}. It is discounted by {percent}%, and then a "
        f"${shipping} shipping fee is added. What is the final cost?"
    )
    steps = [
        f"The discount is {percent}% of ${price}: ${price} x {percent} / 100 "
        f"= ${discount}.",
        f"The sale price is ${price} - ${discount} = ${price - discount}.",
        f"Adding the ${shipping} shipping fee gives "
        f"${price - discount} + ${shipping} = ${final}.",
    ]
    return make_example(
        "math", "medium", question, steps, f"${final}", "discount",
    )


def math_production(rng: random.Random) -> dict[str, Any]:
    rate = rng.randint(12, 60)
    hours = rng.randint(2, 8)
    lost = rng.randint(5, min(60, hours * 60 - 1))
    effective_minutes = hours * 60 - lost
    produced = rate * effective_minutes
    question = (
        f"A machine produces {rate} parts per minute. It runs for {hours} hours, "
        f"but {lost} minutes are lost to maintenance. How many parts does it "
        "produce?"
    )
    steps = [
        f"{hours} hours is {hours} x 60 = {hours * 60} minutes.",
        f"With {lost} minutes lost, the machine runs for "
        f"{hours * 60} - {lost} = {effective_minutes} minutes.",
        f"At {rate} parts per minute, it produces "
        f"{rate} x {effective_minutes} = {produced} parts.",
    ]
    return make_example(
        "math", "medium", question, steps, f"{produced} parts", "production",
    )


def math_gardens(rng: random.Random) -> dict[str, Any]:
    length_a = rng.randint(5, 25)
    width_a = rng.randint(3, 20)
    length_b = rng.randint(6, 28)
    width_b = rng.randint(4, 22)
    area_a = length_a * width_a
    area_b = length_b * width_b
    while area_a == area_b:
        length_b = rng.randint(6, 28)
        width_b = rng.randint(4, 22)
        area_b = length_b * width_b
    larger = max(area_a, area_b)
    smaller = min(area_a, area_b)
    difference = larger - smaller
    question = (
        f"A rectangular garden is {length_a} m by {width_a} m. A second "
        f"rectangular garden is {length_b} m by {width_b} m. How much larger "
        "is the area of the larger garden?"
    )
    steps = [
        f"The first garden has area {length_a} x {width_a} = {area_a} square "
        "meters.",
        f"The second garden has area {length_b} x {width_b} = {area_b} square "
        "meters.",
        f"The larger area is {larger} and the smaller is {smaller}, so the "
        f"difference is {larger} - {smaller} = {difference} square meters.",
    ]
    return make_example(
        "math", "medium", question, steps,
        f"{difference} square meters", "area_difference",
    )


def math_examples(rng: random.Random) -> list[dict[str, Any]]:
    builders = [math_inventory, math_discount, math_production, math_gardens]
    examples: list[dict[str, Any]] = []
    seen: set[str] = set()
    while len(examples) < TRAIN_PER_CATEGORY + EVAL_PER_CATEGORY:
        example = builders[len(examples) % len(builders)](rng)
        if example["question"] in seen:
            continue
        seen.add(example["question"])
        examples.append(example)
    return examples


THEMES = [
    {
        "kind": "race",
        "intro": "Five runners finished a race with no ties. The runners are {names}.",
        "before": "finished before",
        "immediate": "finished immediately before",
        "question": "What was the finishing order from first to last?",
        "join": " -> ",
    },
    {
        "kind": "line",
        "intro": "Five students stand in a line from left to right. The students are {names}.",
        "before": "is somewhere to the left of",
        "immediate": "is immediately to the left of",
        "question": "What is the order from left to right?",
        "join": " -> ",
    },
    {
        "kind": "shelf",
        "intro": "Five books sit on a shelf from left to right. The books are {names}.",
        "before": "is somewhere to the left of",
        "immediate": "is immediately to the left of",
        "question": "What is the order from left to right?",
        "join": " -> ",
    },
]


def logic_examples(rng: random.Random) -> list[dict[str, Any]]:
    examples: list[dict[str, Any]] = []
    seen: set[str] = set()
    while len(examples) < TRAIN_PER_CATEGORY + EVAL_PER_CATEGORY:
        names = rng.sample(NAMES, 5)
        order = rng.sample(names, 5)
        theme = rng.choice(THEMES)
        p0, p1, p2, p3, p4 = order
        clues = [
            f"{p0} {theme['before']} {p2}.",
            f"{p2} {theme['before']} {p1}.",
            f"{p1} {theme['immediate']} {p3}.",
            f"{p3} {theme['immediate']} {p4}.",
        ]
        rng.shuffle(clues)
        clue_text = " ".join(
            f"({index}) {clue}" for index, clue in enumerate(clues, 1)
        )
        question = (
            f"{theme['intro'].format(names=', '.join(names))} "
            f"The following facts are known: {clue_text} {theme['question']}"
        )
        if question in seen:
            continue
        seen.add(question)
        answer = theme["join"].join((p0, p2, p1, p3, p4))
        steps = [
            f"The two immediate-order clues place {p1}, {p3}, and {p4} "
            "consecutively in that order.",
            f"The clue that {p2} is before {p1} puts {p2} ahead of that block, "
            f"and the clue that {p0} is before {p2} puts {p0} first.",
            f"Chaining the clues therefore gives {answer}.",
        ]
        examples.append(make_example(
            "logic", "medium", question, steps, answer, theme["kind"],
        ))
    return examples


CODING_TEMPLATES = [
    {
        "name": "sum_even_squares",
        "signature": "sum_even_squares(nums)",
        "description": "returns the sum of the squares of every even number in nums",
        "code": """def sum_even_squares(nums):
    total = 0
    for number in nums:
        if number % 2 == 0:
            total += number * number
    return total""",
        "steps": [
            "Initialize a running total to zero.",
            "Loop through each number in nums and test whether it is even.",
            "For each even number, add its square to the total.",
            "Return the accumulated total.",
        ],
        "samples": [
            [1, 2, 3, 4], [2, 4, 6], [5, 10, 15, 20], [7, 8, 9, 10],
        ],
    },
    {
        "name": "count_vowels",
        "signature": "count_vowels(text)",
        "description": "counts the vowels a, e, i, o, and u in text, ignoring case",
        "code": """def count_vowels(text):
    vowels = "aeiou"
    return sum(1 for char in text.lower() if char in vowels)""",
        "steps": [
            "Convert the text to lowercase so uppercase vowels count too.",
            "Inspect each character and test membership in a, e, i, o, u.",
            "Count the matching characters and return the count.",
        ],
        "samples": [
            "reasoning is fun", "Chain of Thought", "HELLO world", "a e i o u",
        ],
    },
    {
        "name": "reverse_words",
        "signature": "reverse_words(sentence)",
        "description": "reverses the order of words in sentence while keeping each word intact",
        "code": """def reverse_words(sentence):
    return " ".join(reversed(sentence.split()))""",
        "steps": [
            "Split the sentence on whitespace into a list of words.",
            "Reverse the list of words.",
            "Join the reversed words back into one string with single spaces.",
        ],
        "samples": [
            "hello world", "one two three", "reason step by step", "a b c",
        ],
    },
    {
        "name": "is_palindrome",
        "signature": "is_palindrome(text)",
        "description": "returns True when text is a palindrome after ignoring case and non-alphanumeric characters",
        "code": """def is_palindrome(text):
    cleaned = [char.lower() for char in text if char.isalnum()]
    return cleaned == cleaned[::-1]""",
        "steps": [
            "Normalize the text by lowercasing alphanumeric characters and "
            "dropping punctuation and spaces.",
            "Compare the cleaned sequence with its reverse.",
            "Return True when both sequences match, otherwise False.",
        ],
        "samples": [
            "A man, a plan, a canal: Panama", "racecar", "hello",
            "Was it a car or a cat I saw?",
        ],
    },
    {
        "name": "fizzbuzz",
        "signature": "fizzbuzz(n)",
        "description": "returns the FizzBuzz list for integers 1 through n",
        "code": """def fizzbuzz(n):
    result = []
    for number in range(1, n + 1):
        if number % 15 == 0:
            result.append("FizzBuzz")
        elif number % 3 == 0:
            result.append("Fizz")
        elif number % 5 == 0:
            result.append("Buzz")
        else:
            result.append(str(number))
    return result""",
        "steps": [
            "Create an empty result list and iterate from 1 through n.",
            "Check divisibility by 15 first, then by 3, then by 5.",
            "Append FizzBuzz, Fizz, Buzz, or the number as a string.",
            "Return the completed list.",
        ],
        "samples": [6, 10, 15, 20],
    },
    {
        "name": "fibonacci",
        "signature": "fibonacci(n)",
        "description": "returns a list of the first n Fibonacci numbers starting with 0 and 1",
        "code": """def fibonacci(n):
    if n <= 0:
        return []
    if n == 1:
        return [0]
    sequence = [0, 1]
    while len(sequence) < n:
        sequence.append(sequence[-1] + sequence[-2])
    return sequence""",
        "steps": [
            "Handle n <= 0 by returning an empty list.",
            "Start the sequence with 0 and 1, handling n == 1 separately.",
            "While the sequence is too short, append the sum of its last two values.",
            "Return the first n Fibonacci numbers.",
        ],
        "samples": [5, 7, 9, 12],
    },
    {
        "name": "second_largest",
        "signature": "second_largest(nums)",
        "description": "returns the second largest distinct value in nums",
        "code": """def second_largest(nums):
    unique = sorted(set(nums), reverse=True)
    if len(unique) < 2:
        return None
    return unique[1]""",
        "steps": [
            "Remove duplicate values so repeated copies do not count as the "
            "second-largest value.",
            "Sort the distinct values in descending order.",
            "Return the value at index 1, or None when there are fewer than two "
            "distinct values.",
        ],
        "samples": [
            [3, 1, 4, 1, 5], [10, 20, 30], [5, 5, 7, 7], [9, 8, 7, 6],
        ],
    },
    {
        "name": "flatten",
        "signature": "flatten(matrix)",
        "description": "flattens a matrix of rows into a single list in row-major order",
        "code": """def flatten(matrix):
    result = []
    for row in matrix:
        result.extend(row)
    return result""",
        "steps": [
            "Create an empty result list.",
            "Visit each row of the matrix in order.",
            "Extend the result with every element of the current row.",
            "Return the flattened list.",
        ],
        "samples": [
            [[1, 2], [3, 4]], [[1], [2, 3], [4]], [[5, 6, 7]],
            [[], [1, 2], []],
        ],
    },
    {
        "name": "char_frequency",
        "signature": "char_frequency(text)",
        "description": "returns a dictionary mapping each character in text to its frequency",
        "code": """def char_frequency(text):
    frequencies = {}
    for char in text:
        frequencies[char] = frequencies.get(char, 0) + 1
    return frequencies""",
        "steps": [
            "Create an empty frequency dictionary.",
            "Visit every character and increment its current count.",
            "Use a default of zero when a character is seen for the first time.",
            "Return the completed dictionary.",
        ],
        "samples": ["banana", "reasoning", "mississippi", "abcabc"],
    },
    {
        "name": "celsius_to_fahrenheit",
        "signature": "celsius_to_fahrenheit(celsius)",
        "description": "converts a Celsius temperature to Fahrenheit",
        "code": """def celsius_to_fahrenheit(celsius):
    return celsius * 9 / 5 + 32""",
        "steps": [
            "Multiply the Celsius value by 9.",
            "Divide the product by 5.",
            "Add 32 and return the Fahrenheit value.",
        ],
        "samples": [0, 25, 37, -5],
    },
    {
        "name": "gcd",
        "signature": "gcd(a, b)",
        "description": "returns the greatest common divisor of two positive integers",
        "code": """def gcd(a, b):
    while b != 0:
        a, b = b, a % b
    return abs(a)""",
        "steps": [
            "Use the Euclidean algorithm with a and b.",
            "Replace a and b with b and the remainder of a divided by b.",
            "Repeat until the remainder is zero.",
            "Return the last nonzero value as the greatest common divisor.",
        ],
        "samples": [(48, 18), (84, 30), (1071, 462), (270, 192)],
    },
    {
        "name": "is_anagram",
        "signature": "is_anagram(first, second)",
        "description": "returns True when the two strings are anagrams after ignoring case and spaces",
        "code": """def is_anagram(first, second):
    def normalize(value):
        return sorted(value.replace(" ", "").lower())
    return normalize(first) == normalize(second)""",
        "steps": [
            "Normalize each string by removing spaces and lowercasing it.",
            "Sort the characters of both normalized strings.",
            "Compare the sorted character sequences and return the boolean result.",
        ],
        "samples": [
            ("listen", "silent"), ("evil", "vile"), ("hello", "world"),
            ("Dormitory", "dirty room"),
        ],
    },
]


def run_code(code: str, name: str, arguments: tuple[Any, ...]) -> Any:
    namespace: dict[str, Any] = {}
    exec(code, namespace)
    return namespace[name](*arguments)


def coding_examples(rng: random.Random) -> list[dict[str, Any]]:
    examples: list[dict[str, Any]] = []
    seen: set[str] = set()
    for template in CODING_TEMPLATES:
        for sample in template["samples"]:
            arguments = sample if isinstance(sample, tuple) else (sample,)
            expected = run_code(template["code"], template["name"], arguments)
            call = f"{template['name']}({', '.join(repr(arg) for arg in arguments)})"
            question = (
                f"Write a Python function `{template['signature']}` that "
                f"{template['description']}. For example, `{call}` should return "
                f"`{expected!r}`. Show your reasoning, then return the function "
                "implementation in a Python code block."
            )
            if question in seen:
                continue
            seen.add(question)
            code_target = f"```python\n{template['code']}\n```"
            examples.append(make_example(
                "coding", "medium", question, template["steps"], code_target,
                "python_function",
                {"sample_input": sample, "sample_output": expected,
                 "function_name": template["name"]},
            ))
    if len(examples) != TRAIN_PER_CATEGORY + EVAL_PER_CATEGORY:
        raise RuntimeError(
            f"coding generated {len(examples)} rows, expected 48"
        )
    return examples


def validate_example(example: dict[str, Any]) -> None:
    assistant = example["messages"][-1]["content"]
    if assistant.count("<think>") != 1 or assistant.count("</think>") != 1:
        raise ValueError("invalid think tags in %s" % example.get("id"))
    start = assistant.index("<think>") + len("<think>")
    end = assistant.index("</think>")
    if not assistant[start:end].strip():
        raise ValueError("empty think block in %s" % example.get("id"))
    if not assistant[end + len("</think>"):].strip():
        raise ValueError("missing final answer in %s" % example.get("id"))


def render_example(tokenizer: Any, example: dict[str, Any]) -> None:
    text = tokenizer.apply_chat_template(
        example["messages"], tokenize=False, add_generation_prompt=False
    )
    example["text"] = text
    example["tokens"] = len(tokenizer(text, add_special_tokens=False)["input_ids"])


def split_categories(
    examples: list[dict[str, Any]], rng: random.Random
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rng.shuffle(examples)
    return examples[:TRAIN_PER_CATEGORY], examples[TRAIN_PER_CATEGORY:]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    os.replace(temporary, path)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate a deterministic synthetic reasoning SFT dataset."
    )
    parser.add_argument("--tokenizer", default=str(DEFAULT_TOKENIZER))
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT))
    parser.add_argument("--seed", type=int, default=20261105)
    args = parser.parse_args()

    tokenizer_path = Path(args.tokenizer).expanduser().resolve()
    out_dir = Path(args.out_dir).expanduser().resolve()
    if not tokenizer_path.is_dir():
        raise FileNotFoundError(f"Tokenizer directory not found: {tokenizer_path}")
    out_dir.mkdir(parents=True, exist_ok=True)

    rng = random.Random(args.seed)
    category_rows: dict[str, list[dict[str, Any]]] = {}
    for category, builder in (
        ("math", math_examples),
        ("logic", logic_examples),
        ("coding", coding_examples),
    ):
        rows = builder(rng)
        expected = TRAIN_PER_CATEGORY + EVAL_PER_CATEGORY
        if len(rows) != expected:
            raise RuntimeError(
                f"{category}: generated {len(rows)} rows, expected {expected}"
            )
        category_rows[category] = rows

    train_rows: list[dict[str, Any]] = []
    eval_rows: list[dict[str, Any]] = []
    split_rng = random.Random(args.seed + 1)
    for category, rows in category_rows.items():
        split_rng.shuffle(rows)
        category_train = rows[:TRAIN_PER_CATEGORY]
        category_eval = rows[TRAIN_PER_CATEGORY:]
        for row in category_train:
            row["metadata"]["split"] = "train"
            row["id"] = f"reason_train_{category}_{len(train_rows) + 1:04d}"
            train_rows.append(row)
        for row in category_eval:
            row["metadata"]["split"] = "eval"
            row["id"] = f"reason_eval_{category}_{len(eval_rows) + 1:04d}"
            eval_rows.append(row)

    all_questions = [row["question"] for row in train_rows + eval_rows]
    if len(all_questions) != len(set(all_questions)):
        raise RuntimeError("duplicate questions across train/eval")
    if len(train_rows) != 120 or len(eval_rows) != 24:
        raise RuntimeError("unexpected split sizes")

    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(
        str(Path(args.tokenizer).expanduser().resolve()), local_files_only=True
    )
    for row in train_rows + eval_rows:
        validate_example(row)
        render_example(tokenizer, row)

    out_dir = Path(args.out_dir).expanduser().resolve()
    train_path = out_dir / "reasoning_train.jsonl"
    eval_path = out_dir / "reasoning_eval.jsonl"
    write_jsonl(train_path, train_rows)
    write_jsonl(eval_path, eval_rows)

    train_tokens = [row["tokens"] for row in train_rows]
    eval_tokens = [row["tokens"] for row in eval_rows]
    counts = {
        "train": len(train_rows),
        "eval": len(eval_rows),
        "by_category": {
            category: {
                "train": sum(1 for row in train_rows
                             if row["category"] == category),
                "eval": sum(1 for row in eval_rows
                            if row["category"] == category),
            }
            for category in CATEGORIES
        },
    }
    summary = {
        "suite": "phase6-reasoning-v1",
        "seed": args.seed,
        "tokenizer": str(Path(args.tokenizer).expanduser().resolve()),
        "counts": counts,
        "tokens": {
            "train_min": min(train_tokens),
            "train_mean": round(sum(train_tokens) / len(train_tokens), 2),
            "train_max": max(train_tokens),
            "eval_min": min(eval_tokens),
            "eval_mean": round(sum(eval_tokens) / len(eval_tokens), 2),
            "eval_max": max(eval_tokens),
        },
        "hashes": {
            "train_sha256": sha256_file(train_path),
            "eval_sha256": sha256_file(eval_path),
        },
        "example_ids": {
            "train": train_rows[0]["id"],
            "eval": eval_rows[0]["id"],
        },
    }
    summary_path = out_dir / "dataset_summary.json"
    temporary = summary_path.with_suffix(".json.tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, sort_keys=True)
        handle.write("\n")
    os.replace(temporary, summary_path)

    print("=" * 72)
    print("Phase 6 reasoning dataset")
    print("=" * 72)
    print("train       :", len(train_rows))
    print("eval        :", len(eval_rows))
    print("categories  :", counts["by_category"])
    print("train tokens:", min(train_tokens), "/",
          round(sum(train_tokens) / len(train_tokens), 2), "/", max(train_tokens))
    print("eval tokens :", min(eval_tokens), "/",
          round(sum(eval_tokens) / len(eval_tokens), 2), "/", max(eval_tokens))
    print("train sha256:", summary["hashes"]["train_sha256"])
    print("eval sha256 :", summary["hashes"]["eval_sha256"])
    print("summary     :", summary_path)
    print("RESULT: PHASE6_REASONING_DATASET_OK train=%d eval=%d "
          "categories=%s train_sha256=%s eval_sha256=%s"
          % (len(train_rows), len(eval_rows), counts["by_category"],
             summary["hashes"]["train_sha256"],
             summary["hashes"]["eval_sha256"]), flush=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as exc:
        import traceback
        traceback.print_exc()
        print("RESULT: PHASE6_REASONING_DATASET_FAIL %s" % exc, file=sys.stderr, flush=True)
        print("RESULT: PHASE6_REASONING_DATASET_FAIL %s" % exc, flush=True)
        raise SystemExit(1)
