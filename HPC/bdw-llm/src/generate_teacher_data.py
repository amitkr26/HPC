"""Stage N.2: teacher generation on the GPU node (offline -- no network here).

Loads Qwen2.5-7B-Instruct from the local directory written by Step N.1 and
answers a prompt pack of ~528: a domain pack of VLSI / semiconductor / career
questions (what BDW actually cares about) plus a Dolly-15k subset for general
instruction diversity.

Sequence-level distillation, not logit distillation: the student owns a custom
16,384-token byte-level BPE, so the teacher's 151,643-token vocab has no
aligned logits to match and KL divergence is undefined. We keep only the
teacher's TEXT; Step N.3 re-encodes it with the student's own tokenizer using
the exact Stage K template.

Teacher selection was measured, not assumed (pilot job 32336):
  0.5B - invented "ATPG = Automated Testing Program Generator" (software) and
         called STA a software technique. Rejected.
  1.5B - right domain/acronyms, but fabricated specifics: described corner
         simulation as a digital truth table and claimed buffers fix setup by
         "adding delay". Rejected -- sequence-level KD copies the teacher's
         knowledge INCLUDING ITS ERRORS.
  7B   - textbook-correct on setup/hold, names stuck-at fault models, defines
         CDC/metastability properly. Chosen for accuracy over speed.

GRACEFUL SAVE/RESUME (15-min MaxWall): every finished row is written and
flushed immediately, and resume keys on a hash of the QUESTION. If the job is
killed at the wall limit it stops with ~4 min of margin, and the next
`sbatch scripts/run_teacher.slurm` picks up exactly the prompts that are
missing -- no duplicates, no lost rows. Submit repeatedly until it prints
RESULT: N2_TEACHER_GENERATION_OK.
"""
import hashlib
import json
import os
import re
import time

os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

ROOT = os.path.expanduser("~/bdw-llm")
TEACHER = os.path.join(ROOT, "teacher_model_7b")
TEACHER_ID = "Qwen/Qwen2.5-7B-Instruct"
DOLLY = os.path.join(ROOT, "data/raw/dolly15k.jsonl")
OUT = os.path.join(ROOT, "data/distilled_teacher_data.jsonl")
LIMIT = 11 * 60         # stop with ~4 min of walltime left for the final flush
BATCH = 8               # measured 1.39 prompts/s on the A100 (pilot job 32336)
MAX_NEW = 224
TEMP, TOP_P = 0.3, 0.9  # low temperature: factual stability over diversity
SEED = 1234
DOLLY_PER_CAT = 40      # 8 categories -> 320 dolly rows
MIN_WORDS = 30          # N.3 drops answers shorter than this

# ---------------------------------------------------------------- prompts
DOMAIN = [
    ("digital", "Explain the difference between a setup violation and a hold violation in static timing analysis."),
    ("digital", "Why can a hold violation not be fixed by adding a clock delay?"),
    ("digital", "What is clock skew and how does it differ from clock jitter?"),
    ("digital", "Explain the purpose of clock tree synthesis in physical design."),
    ("digital", "What is the role of a Phase Locked Loop in a mixed signal chip?"),
    ("digital", "Why is CMOS technology preferred over Bipolar and GaAs in VLSI design?"),
    ("digital", "What does Moore's Law actually predict, and why is it not a physical law?"),
    ("digital", "Explain the difference between Mealy and Moore state machines with an example."),
    ("digital", "What is a metastability condition and how do synchronizers prevent it?"),
    ("digital", "Explain how a two flip flop synchronizer works and when it is insufficient."),
    ("digital", "What is the purpose of a reset in a digital design, and synchronous vs asynchronous reset?"),
    ("digital", "Explain pipelining in a processor and identify a structural hazard."),
    ("digital", "What is bus contention and how is it avoided?"),
    ("digital", "Explain the working of a dynamic flip flop versus a static flip flop."),
    ("digital", "What is the difference between combinational and sequential logic?"),
    ("digital", "What is a race condition in a synchronous design and how do you avoid it?"),
    ("digital", "Explain why a dual edge triggered flip flop halves the required clock frequency."),
    ("digital", "What is glitching in combinational logic and when does it become a problem?"),
    ("digital", "Explain the difference between asynchronous and synchronous reset recovery."),
    ("digital", "What is a clock gating cell and what problem does it solve?"),
    ("digital", "Explain priority encoder versus simple encoder with a truth table example."),
    ("digital", "What is the difference between a ripple counter and a synchronous counter?"),
    ("digital", "Explain how a Johnson counter differs from a ring counter."),
    ("digital", "What is a barrel shifter and where is it used in a processor?"),
    ("digital", "Explain why high fanout nets need buffering in a design."),
    ("rtl", "Write Verilog code for a parameterized FIFO and explain the full and empty flags."),
    ("rtl", "What is the difference between blocking and non blocking assignment in Verilog?"),
    ("rtl", "Explain the purpose of generate blocks in SystemVerilog."),
    ("rtl", "What is clock domain crossing and how do you safely transfer a signal between two clocks?"),
    ("rtl", "Write a Verilog always block that detects a rising edge on an input signal."),
    ("rtl", "What is one hot encoding and when would you choose it over binary encoding?"),
    ("rtl", "Explain lint clean coding and why a design house enforces it."),
    ("rtl", "What is the difference between a task and a function in SystemVerilog?"),
    ("rtl", "Describe a simple arbiter design that grants a resource to one requester at a time."),
    ("rtl", "What is a latch and why do most design guidelines forbid inferring one?"),
    ("rtl", "Explain the difference between a wire and a reg in Verilog and when each is used."),
    ("rtl", "What are the implications of using a for loop inside an always block?"),
    ("rtl", "Write SystemVerilog code for a 4 bit up down counter with synchronous enable."),
    ("rtl", "Explain what a scoreboard compares in a bus protocol testbench."),
    ("rtl", "What is the difference between an interface and a modport in SystemVerilog?"),
    ("rtl", "Describe how you would implement a round robin arbiter in RTL."),
    ("rtl", "What is a gray code pointer and why does an asynchronous FIFO need one?"),
    ("rtl", "Explain handshake based flow control between two modules."),
    ("rtl", "What is the difference between parameter, localparam and define?"),
    ("rtl", "Write Verilog code that safely crosses a multi bit bus using a request acknowledge scheme."),
    ("rtl", "Explain what happens when you use non blocking assignment inside a combinational always block."),
    ("rtl", "How do you detect and prevent unintended priority inversion in an always block?"),
    ("verification", "What is UVM and why has it become the standard verification methodology?"),
    ("verification", "Explain the structure of a UVM testbench with its major components."),
    ("verification", "What is constrained random verification and how does it differ from directed tests?"),
    ("verification", "Explain what a scoreboard does in a verification environment."),
    ("verification", "What is the difference between functional coverage and code coverage?"),
    ("verification", "Describe the UVM phases in order and their purpose."),
    ("verification", "What is a testbench driver and how does it differ from a monitor?"),
    ("verification", "Explain what an agent contains in UVM and why it is reusable."),
    ("verification", "What is the purpose of a coverage driven verification plan?"),
    ("verification", "How do you debug a failing test in a regression run?"),
    ("verification", "Explain the difference between a unit testbench and a full chip testbench."),
    ("verification", "What is backdoor checking versus front door checking in verification?"),
    ("verification", "Describe how an assertions based verification plan differs from a functional one."),
    ("verification", "What is protocol checking and which AXI checks would you always write?"),
    ("verification", "Explain what a reactive testbench is and how it differs from a directed one."),
    ("verification", "What is the role of a virtual sequence in UVM?"),
    ("verification", "Explain how you verify a reset sequence in a design."),
    ("verification", "What is randomization stability and why does a seed matter in a regression?"),
    ("verification", "Describe what closure means for functional and code coverage."),
    ("verification", "How would you isolate a single failing transaction in a noisy log?"),
    ("verification", "What is the difference between a smoke test and a full regression?"),
    ("verification", "Explain why a testbench must be able to run in both batch and interactive modes."),
    ("physical", "Explain the physical design flow from netlist to GDSII."),
    ("physical", "What is floorplanning and why does it matter for timing?"),
    ("physical", "Explain placement, clock tree synthesis and routing in order."),
    ("physical", "What is design rule checking and what kinds of rules does it enforce?"),
    ("physical", "Explain why a hold violation is fixed by adding delay buffers rather than resizing."),
    ("physical", "What is IR drop and how does it affect a chip?"),
    ("physical", "Explain signal crosstalk and how it is mitigated."),
    ("physical", "What is multi corner multi mode analysis?"),
    ("physical", "Why is power planning done before placement?"),
    ("physical", "What is the purpose of dummy fill during metal density control?"),
    ("physical", "Explain what congestion is and how a designer relieves it."),
    ("physical", "What is the difference between global routing and detailed routing?"),
    ("physical", "Explain how a placer decides cell locations and what timing driven placement means."),
    ("physical", "What is a timing bottleneck and how does buffer insertion help?"),
    ("physical", "Explain why hold fixing is done after setup optimization, not before."),
    ("physical", "What is antenna effect in routing and how is it prevented?"),
    ("physical", "Explain the role of a liberty library in physical design."),
    ("physical", "What is the difference between a macro and a standard cell in a floorplan?"),
    ("physical", "Why does a blockage guide placement away from a macro pin cluster?"),
    ("physical", "Explain what signoff means and which checks it includes."),
    ("dft", "What is design for testability and why do fabricated chips need it?"),
    ("dft", "Explain scan chain insertion and how it makes a design testable."),
    ("dft", "What is ATPG and what kind of faults does it target?"),
    ("dft", "Explain the difference between stuck at fault and transition fault testing."),
    ("dft", "What is a built in self test and when is it used?"),
    ("dft", "Why are controllability and observability important for testing?"),
    ("dft", "What is the difference between scan test and boundary scan testing?"),
    ("dft", "Explain what compression means in DFT and why it reduces test time."),
    ("dft", "What is a test access mechanism in an SoC?"),
    ("dft", "Explain how JTAG is used to test a board level design."),
    ("dft", "What is a memory BIST and what faults does it cover?"),
    ("dft", "Why must DFT be planned before RTL is written?"),
    ("dft", "Explain the difference between fault coverage and defect coverage."),
    ("dft", "What is the impact of low power modes on scan testing?"),
    ("dft", "Explain what a test coverage hole is and how a DFT engineer closes it."),
    ("dft", "What is the purpose of a test protocol in an ATPG run?"),
    ("dft", "Why do asynchronous resets complicate scan insertion?"),
    ("dft", "Explain how you test a design that contains an embedded processor core."),
    ("dft", "What is the difference between at speed and slow scan testing?"),
    ("dft", "How does DFT interact with functional safety requirements such as ISO 26262?"),
    ("analog", "Explain the difference between an ADC and a DAC and give a use case for each."),
    ("analog", "What is a SerDes and where is it used in modern chips?"),
    ("analog", "Explain how a bandgap reference produces a stable voltage."),
    ("analog", "What is negative temperature coefficient and why does it matter?"),
    ("analog", "Explain the operation of a sample and hold circuit."),
    ("analog", "What is the purpose of an operational amplifier in an analog front end?"),
    ("analog", "Explain what resolution and accuracy mean for an ADC."),
    ("analog", "What is signal to noise ratio and why is it a headline ADC spec?"),
    ("analog", "Explain the difference between SAR, pipeline and sigma delta ADC architectures."),
    ("analog", "What is a low noise amplifier and where does it sit in a receiver chain?"),
    ("analog", "Explain how a charge pump works inside a PLL."),
    ("analog", "What is layout matching and why do analog designers care so much about it?"),
    ("analog", "Explain common mode rejection and why it matters in an instrumentation amplifier."),
    ("analog", "What is the difference between an analog IP block and a digital IP block in a PDK?"),
    ("analog", "Explain what corner simulation covers for an analog block."),
    ("analog", "What is electromigration and how does it constrain analog current mirrors?"),
    ("analog", "Explain the role of decoupling capacitors in a mixed signal chip."),
    ("analog", "What is substrate noise and how does digital switching disturb analog blocks?"),
    ("analog", "Explain how you would verify an analog block before silicon."),
    ("analog", "What is the difference between pre layout and post layout simulation?"),
    ("fab", "Explain the semiconductor manufacturing flow from wafer to packaged part."),
    ("fab", "What is lithography and why is it the most critical step in fabrication?"),
    ("fab", "What is doping and why is it done to silicon?"),
    ("fab", "Why is silicon the dominant semiconductor material in the industry?"),
    ("fab", "What does tape out mean in chip design?"),
    ("fab", "Explain FinFET and Gate All Around transistor architectures and why they were needed."),
    ("fab", "What is the difference between front end of line and back end of line?"),
    ("fab", "What is yield and what causes yield loss?"),
    ("fab", "Explain what ATMP and OSAT mean in the semiconductor supply chain."),
    ("fab", "What is a fabless company and how does it differ from an IDM?"),
    ("fab", "Explain what a PDK contains and why designers need one."),
    ("fab", "What is a wafer fab and what does it mean to have a fab at 300 mm?"),
    ("fab", "Explain what high k metal gate was introduced to solve."),
    ("fab", "What is a process design kit corner and how many corners does a typical node have?"),
    ("fab", "Explain why advanced packaging is now as important as transistor scaling."),
    ("fab", "What is EUV lithography and which layers use it?"),
    ("fab", "Explain what a defect limited yield ramp looks like."),
    ("fab", "What is the difference between a mask and a reticle?"),
    ("fab", "Why do chips need burn in and what failure mode does it screen out?"),
    ("fab", "Explain what chiplets change about how a company ships a product."),
    ("career", "How should a fresher prepare for a VLSI job interview?"),
    ("career", "Which EDA tools should a student learn to enter the semiconductor industry?"),
    ("career", "What is the difference between a Design Verification role and a Physical Design role?"),
    ("career", "What skills are required for an entry level RTL design engineer?"),
    ("career", "Explain what a Junior Research Fellowship is and who is eligible in India."),
    ("career", "What is the difference between JRF and SRF in terms of stipend and tenure?"),
    ("career", "How does DRDO recruit scientists and what is the RAC portal?"),
    ("career", "What preparation is needed for GATE Electronics to secure a good rank?"),
    ("career", "What kind of projects should a fresher build to impress a semiconductor recruiter?"),
    ("career", "Explain the career growth path from verification engineer to design lead."),
    ("career", "What is the difference between a VLSI design engineer and an embedded systems engineer?"),
    ("career", "How should one build a hardware resume that passes an ATS screen?"),
    ("career", "What are the typical roles available at a fabless design house in India?"),
    ("career", "Explain the difference between an internship and a full time role at a chip company."),
    ("career", "Which Indian companies hire electronics engineers for VLSI work?"),
    ("career", "What does an ISRO recruitment process look like for a electronics graduate?"),
    ("career", "How is a CSIR laboratory different from a DRDO laboratory for a research career?"),
    ("career", "What is the role of a design engineer versus an application engineer at an EDA company?"),
    ("career", "Explain what a fresher should expect in a technical screening round."),
    ("career", "How long does it typically take to become an independent verification owner?"),
    ("career", "What is the value of a masters degree for a career in chip design?"),
    ("career", "Which open source tools can a student practise with without an EDA licence?"),
    ("career", "Explain how job portals and daily scrapers help a candidate track openings."),
    ("career", "What salary band should a fresher expect in Indian VLSI roles?"),
    ("career", "How should a career switcher from software move into hardware verification?"),
    ("career", "What is the difference between a product company and a services company in semiconductors?"),
    ("open", "What is a transistor and how does it switch?"),
    ("open", "Explain why low power design matters in mobile SoCs."),
    ("open", "What is power gating and how does it save energy?"),
    ("open", "Explain the difference between dynamic and static power consumption."),
    ("open", "What is voltage scaling and why is it used?"),
    ("open", "Explain what an SoC is and name three of its major subsystems."),
    ("open", "What is a RISC-V core and why is it significant for Indian chip design?"),
    ("open", "Explain what an IP core is in semiconductor design."),
    ("open", "What is the difference between a microcontroller and a microprocessor?"),
    ("open", "Explain how an instruction set architecture affects software and hardware."),
    ("open", "What is hardware security and why are side channel attacks a concern?"),
    ("open", "Explain what chiplets and UCIe are and why the industry is moving to them."),
    ("open", "What is hardware in the loop verification?"),
    ("open", "Explain why verification now takes more effort than design."),
    ("open", "What is emulation in hardware verification and when is it used?"),
    ("open", "Explain the difference between FPGA prototyping and ASIC emulation."),
    ("open", "What is formal verification and what properties does it prove?"),
    ("open", "Explain equivalence checking between RTL and gate level netlist."),
    ("open", "What is the difference between synthesis and simulation?"),
    ("open", "Explain what a timing library corner represents."),
    ("open", "What is variation and why does it cause chips to run at different speeds?"),
    ("open", "Explain the concept of PVT corners in chip design."),
    ("open", "What is aging and how does it affect long term reliability of a chip?"),
    ("open", "Explain electro migration and why it limits current in a wire."),
    ("open", "What is the difference between a wafer and a die?"),
    ("open", "Explain what is meant by a tape out schedule slipping and its cost."),
    ("open", "Why does a smaller process node usually mean lower per transistor energy?"),
    ("open", "What is the difference between ASIC and FPGA implementation cost?"),
    ("open", "Explain what functional safety means for an automotive chip."),
    ("open", "What is the difference between reliability and durability in silicon?"),
    ("open", "Explain what happens to a design when the foundry changes a process rule."),
    ("open", "Why is verification of a mixed signal SoC harder than a purely digital one?"),
    ("open", "What is a virtual platform and when is it used in product development?"),
]

DOMAIN_BATCH = [
    "Explain each of the following briefly: {t}.",
    "In a technical interview, how would you answer: {t}?",
    "Give a clear, practical explanation suitable for an electronics engineering student: {t}.",
    "Define {t} and explain why it matters in chip design.",
    "Write a short study note covering {t}, including one example.",
    "I am preparing for a VLSI interview. Explain {t} step by step.",
    "What should a fresher know about {t}? Answer concisely and correctly.",
    "Summarise the key points about {t} that an interviewer expects.",
    "Answer this engineering question with a precise explanation: {t}.",
    "Describe {t} in about 120 words, mentioning its practical relevance.",
]


def qkey(question):
    """Stable identity for a prompt, independent of list position."""
    return hashlib.md5(question.strip().encode("utf-8")).hexdigest()[:16]


def build_prompts():
    prompts = []
    seen = set()
    for cat, text in DOMAIN:
        variant = DOMAIN_BATCH[int(qkey(text)[:8], 16) % len(DOMAIN_BATCH)]
        q = variant.format(t=text)
        if q in seen:
            continue
        seen.add(q)
        prompts.append({"id": qkey(q), "category": cat, "source": "domain",
                        "question": q})
    if os.path.exists(DOLLY):
        by_cat = {}
        with open(DOLLY, encoding="utf-8") as fh:
            for line in fh:
                r = json.loads(line)
                instr = (r.get("instruction") or "").strip()
                if not instr:
                    continue
                ctx = (r.get("context") or "").strip()
                cat = r.get("category", "general_qa")
                by_cat.setdefault(cat, []).append(((ctx + "\n\n" + instr) if ctx else instr)[:1500])
        for cat in sorted(by_cat):
            for q in sorted(set(by_cat[cat]), key=qkey)[:DOLLY_PER_CAT]:
                if q in seen:
                    continue
                seen.add(q)
                prompts.append({"id": qkey(q), "category": cat, "source": "dolly",
                                "question": q})
    return prompts


# -------------------------------------------------------------- generation
def main():
    print("=" * 76)
    print("STAGE N.2 - TEACHER GENERATION (GPU node, offline)")
    print("=" * 76)
    print("host    :", os.uname().nodename)
    print("teacher :", TEACHER, "(%s)" % TEACHER_ID)
    print("out     :", OUT)
    if not os.path.exists(os.path.join(TEACHER, "model.safetensors")) and \
       not os.path.exists(os.path.join(TEACHER, "model.safetensors.index.json")):
        raise SystemExit("teacher weights missing -- run Step N.1 on the login node")
    print("weights   : %s"
          % ("model.safetensors"
             if os.path.exists(os.path.join(TEACHER, "model.safetensors"))
             else "sharded (index + 4 safetensors)"))

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    t0 = time.time()
    tok = AutoTokenizer.from_pretrained(TEACHER, local_files_only=True)
    # left padding: correct for batched decoder-only generation
    tok.padding_side = "left"
    model = AutoModelForCausalLM.from_pretrained(
        TEACHER, local_files_only=True, dtype=torch.float16)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = model.to(device).eval()
    print("loaded   : %s on %s in %.1fs"
          % (f"{sum(p.numel() for p in model.parameters()):,}", device, time.time() - t0))
    if device == "cuda":
        print("gpu      :", torch.cuda.get_device_name(0))

    prompts = build_prompts()
    print("prompts  : %d (%d domain + %d dolly)"
          % (len(prompts),
             sum(1 for p in prompts if p["source"] == "domain"),
             sum(1 for p in prompts if p["source"] == "dolly")))
    print("decode   : chat_template=True max_new=%d temp=%.1f top_p=%.1f batch=%d seed=%d"
          % (MAX_NEW, TEMP, TOP_P, BATCH, SEED))

    # ------------------------------------------------- resume by question
    done = set()
    if os.path.exists(OUT):
        with open(OUT, encoding="utf-8") as fh:
            for line in fh:
                try:
                    done.add(qkey(json.loads(line).get("question", "")))
                except Exception:
                    pass
    todo = [p for p in prompts if p["id"] not in done]
    print("resume   : %d already written, %d to generate" % (len(done), len(todo)))
    print()

    torch.manual_seed(SEED)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(SEED)

    n_ok = n_empty = n_boiler = n_leak = n_short = 0
    t_start = time.time()
    with open(OUT, "a", encoding="utf-8") as fh:
        for i in range(0, len(todo), BATCH):
            if time.time() - t_start > LIMIT:
                print("[wall] %d s elapsed, stopping early -- %d prompts left"
                      % (LIMIT, len(todo) - i))
                break
            batch = todo[i:i + BATCH]
            # render each turn through the chat template, then batch-tokenise
            rendered = [tok.apply_chat_template(
                            [{"role": "user", "content": p["question"]}],
                            tokenize=False, add_generation_prompt=True)
                        for p in batch]
            enc = tok(rendered, return_tensors="pt", padding=True,
                      truncation=True, max_length=1536).to(device)
            n_prompt_tok = int(enc["input_ids"].shape[1])
            with torch.no_grad():
                out = model.generate(
                    input_ids=enc["input_ids"],
                    attention_mask=enc["attention_mask"],
                    max_new_tokens=MAX_NEW, do_sample=True,
                    temperature=TEMP, top_p=TOP_P,
                    pad_token_id=tok.pad_token_id or tok.eos_token_id,
                    eos_token_id=tok.eos_token_id)
            gen = out[:, n_prompt_tok:]
            for p, ids in zip(batch, gen):
                ans = tok.decode(ids, skip_special_tokens=True).strip()
                rec = {"id": p["id"], "category": p["category"],
                       "source": p["source"], "question": p["question"],
                       "response": ans, "teacher": TEACHER_ID,
                       "decode": {"chat_template": True, "temperature": TEMP,
                                  "top_p": TOP_P, "max_new_tokens": MAX_NEW,
                                  "seed": SEED}}
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
                fh.flush()
                if not ans:
                    n_empty += 1
                else:
                    n_ok += 1
                    low = ans.lower()
                    if low.startswith(("as an ai", "i'm sorry", "i am sorry", "i cannot")):
                        n_boiler += 1
                    if re.search(r"\bHuman\s*:", ans) or re.search(r"\bAssistant\s*:", ans):
                        n_leak += 1
                    if len(ans.split()) < MIN_WORDS:
                        n_short += 1
            n_done = min(i + BATCH, len(todo))
            rate = n_done / max(time.time() - t_start, 1e-9)
            print("[gen] %d/%d  %.2f prompts/s  elapsed %.0fs  eta %.0fs"
                  % (n_done, len(todo), rate, time.time() - t_start,
                     (len(todo) - n_done) / max(rate, 1e-9)), flush=True)

    # ------------------------------------------------------- verification
    rows = 0
    cats, srcs, ids = {}, {}, set()
    lens = []
    bad = dup = leak = refus = 0
    if os.path.exists(OUT):
        with open(OUT, encoding="utf-8") as fh:
            for line in fh:
                try:
                    r = json.loads(line)
                except Exception:
                    bad += 1
                    continue
                k = qkey(r.get("question", ""))
                if k in ids:
                    dup += 1
                    continue
                ids.add(k)
                rows += 1
                cats[r["category"]] = cats.get(r["category"], 0) + 1
                srcs[r["source"]] = srcs.get(r["source"], 0) + 1
                lens.append(len(r.get("response", "").split()))
                low = r["response"].lower()
                if low.startswith(("as an ai", "i'm sorry", "i am sorry", "i cannot")):
                    refus += 1
                if re.search(r"\bHuman\s*:", r["response"]) or \
                   re.search(r"\bAssistant\s*:", r["response"]):
                    leak += 1

    print()
    print("=" * 76)
    print("VERIFICATION")
    print("=" * 76)
    print("jsonl rows          : %d   (corrupt: %d, duplicate: %d)" % (rows, bad, dup))
    print("file size           : %s" % ("%.2f MB" % (os.path.getsize(OUT) / 1e6)
                                        if os.path.exists(OUT) else "missing"))
    print("non-empty answers   : %d" % n_ok)
    print("empty answers       : %d" % n_empty)
    print("refusal boilerplate : %d" % refus)
    print("Human:/Assistant: leak : %d" % leak)
    print("fewer than %d words  : %d" % (MIN_WORDS, n_short))
    if lens:
        lens.sort()
        print("answer words        : min=%d median=%d mean=%.1f max=%d"
              % (lens[0], lens[len(lens) // 2], sum(lens) / len(lens), lens[-1]))
    print("by source           : %s" % srcs)
    print("domain categories   : %s"
          % {k: v for k, v in sorted(cats.items()) if k in
             ("digital", "rtl", "verification", "physical", "dft", "analog",
              "fab", "career", "open")})
    print("total time          : %.1fs" % (time.time() - t0))
    print()
    ok = (rows >= 500 and bad == 0 and dup == 0 and n_empty == 0
          and leak <= rows * 0.02)
    print("RESULT: N2_TEACHER_GENERATION_%s (%d rows)" % ("OK" if ok else "FAILED", rows))


if __name__ == "__main__":
    main()
