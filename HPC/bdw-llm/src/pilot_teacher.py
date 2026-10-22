"""Stage N.2 pilot: does the 7B teacher actually handle VLSI better than 1.5B?

Runs the same three questions, with the same chat template and greedy decoding,
that were used to judge Qwen2.5-1.5B-Instruct, so the answers are directly
comparable against the recorded 1.5B baselines. Then measures real generation
throughput with the production decode settings so the full-run ETA (and whether
one 15-min job is enough) is known before committing to it.
"""
import json
import os
import time

os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

ROOT = os.path.expanduser("~/bdw-llm")
TEACHER = os.path.join(ROOT, "teacher_model_7b")
DOLLY = os.path.join(ROOT, "data/raw/dolly15k.jsonl")

QS = [
    "Explain the difference between a setup violation and a hold violation in "
    "static timing analysis. Why can a hold violation not be fixed by adding "
    "clock latency?",
    "What does ATPG stand for, what fault models does it target, and why must "
    "it be planned before RTL is written?",
    "Explain what a clock domain crossing is and describe a safe way to move "
    "a single bit between two unrelated clocks.",
]

DOMAIN = [
    "Explain the difference between a setup violation and a hold violation in "
    "static timing analysis.",
    "What is a metastability condition and how do synchronizers prevent it?",
    "Explain scan chain insertion and how it makes a design testable.",
    "What is a gray code pointer and why does an asynchronous FIFO need one?",
    "Explain what corner simulation covers for an analog block.",
    "What is IR drop and how does it affect a chip?",
    "Why must DFT be planned before RTL is written?",
    "Explain how a two flip flop synchronizer works and when it is insufficient.",
    "What is a timing bottleneck and how does buffer insertion help?",
    "Explain the physical design flow from netlist to GDSII.",
    "What is a clock gating cell and what problem does it solve?",
    "What is EUV lithography and which layers use it?",
    "Which EDA tools should a student learn to enter the semiconductor industry?",
    "What is the difference between a Design Verification role and a Physical "
    "Design role?",
    "Explain FinFET and Gate All Around transistor architectures and why they "
    "were needed.",
    "What is power gating and how does it save energy?",
]
N_BENCH = 32
BENCH_BATCH = 8
MAX_NEW = 224
TEMP, TOP_P = 0.3, 0.9


def main():
    print("=" * 76)
    print("STAGE N.2 PILOT - 7B vs 1.5B on VLSI questions (GPU node, offline)")
    print("=" * 76)
    print("host   :", os.uname().nodename)
    print("teacher:", TEACHER)
    if not os.path.exists(os.path.join(TEACHER, "model.safetensors.index.json")):
        raise SystemExit("7B weights missing -- run Step N.1 on the login node")

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    t0 = time.time()
    tok = AutoTokenizer.from_pretrained(TEACHER, local_files_only=True)
    tok.padding_side = "left"
    model = AutoModelForCausalLM.from_pretrained(
        TEACHER, local_files_only=True, dtype=torch.float16)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = model.to(device).eval()
    n = sum(p.numel() for p in model.parameters())
    print("loaded  : %s (%.2f B) on %s in %.1fs" % (f"{n:,}", n / 1e6,
                                                    device, time.time() - t0))
    if device == "cuda":
        print("gpu     :", torch.cuda.get_device_name(0),
              "%.1f GB free" % (torch.cuda.mem_get_info()[0] / 1e9))

    def answer(q, max_new=200):
        ids = tok.apply_chat_template([{"role": "user", "content": q}],
                                      tokenize=True, add_generation_prompt=True,
                                      return_tensors="pt").to(device)
        t = time.time()
        with torch.no_grad():
            out = model.generate(ids, max_new_tokens=max_new, do_sample=False,
                                 eos_token_id=tok.eos_token_id,
                                 pad_token_id=tok.eos_token_id)
        txt = tok.decode(out[0][ids.shape[1]:], skip_special_tokens=True).strip()
        return txt, time.time() - t

    for i, q in enumerate(QS, 1):
        txt, dt = answer(q)
        print()
        print("=" * 76)
        print("Q%d: %s" % (i, q))
        print("-" * 76)
        print("[7B, chat template, greedy, %.1fs]" % dt)
        print(txt)
        print()

    # ---------------------------------------------------- throughput bench
    print("=" * 76)
    print("THROUGHPUT BENCH (production decode: temp %.1f top_p %.1f max_new %d, "
          "batch %d)" % (TEMP, TOP_P, MAX_NEW, BENCH_BATCH))
    print("=" * 76)
    prompts = [(DOMAIN[i % len(DOMAIN)] + " Answer concisely and correctly.")
               for i in range(N_BENCH)]
    t0 = time.time()
    done = 0
    with torch.no_grad():
        for i in range(0, len(prompts), BENCH_BATCH):
            batch = prompts[i:i + BENCH_BATCH]
            rendered = [tok.apply_chat_template([{"role": "user", "content": p}],
                                                tokenize=False,
                                                add_generation_prompt=True)
                        for p in batch]
            enc = tok(rendered, return_tensors="pt", padding=True,
                      truncation=True, max_length=1536).to(device)
            out = model.generate(input_ids=enc["input_ids"],
                                 attention_mask=enc["attention_mask"],
                                 max_new_tokens=MAX_NEW, do_sample=True,
                                 temperature=TEMP, top_p=TOP_P,
                                 pad_token_id=tok.pad_token_id or tok.eos_token_id,
                                 eos_token_id=tok.eos_token_id)
            done += len(batch)
            el = time.time() - t0
            print("[bench] %d/%d  %.2f prompts/s  elapsed %.0fs"
                  % (done, len(prompts), done / el, el), flush=True)
    rate = done / (time.time() - t0)
    print()
    print("measured rate : %.2f prompts/s" % rate)
    print("ETA for 528 prompts : %.0f s generation (+ ~60 s model load)"
          % (528 / max(rate, 1e-9)))
    print("fits one 15-min job : %s" % ("YES" if 528 / max(rate, 1e-9) + 60 < 840
                                        else "NO -- resume across jobs required"))
    print()
    print("RESULT: N2_PILOT_7B_OK (%.2f prompts/s)" % rate)


if __name__ == "__main__":
    main()
