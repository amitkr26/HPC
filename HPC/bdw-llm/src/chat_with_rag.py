"""Stage M: chat with retrieval-augmented generation, on the LOGIN node.

The compute nodes have no DNS, so retrieval has to happen where the network
is -- the login node. The model is small enough (27.8 M parameters, 334 MB)
that inference runs comfortably on the CPU, so no GPU job is needed.

Pipeline:

  1. retrieve  -- Wikipedia first (clean paragraphs, free API), DuckDuckGo
                  as a fallback. Top-k passages are returned.
  2. build     -- the SAME conversational template used to build the Stage K
                  training examples, so prompt and training cannot drift:
                      <|bos|>User: [Question + Context]<|eos|><|bos|>Assistant:
  3. generate  -- CPU inference with the fine-tuned checkpoint, stopping at
                  <|eos|>.

Use --no-rag to answer the same question with no retrieved context, which is
the honest way to see whether retrieval is actually helping.
"""
from __future__ import annotations

import argparse
import os
import random
import sys
import time

import torch
import torch.nn.functional as F
from tokenizers import Tokenizer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from model import ModelConfig, TransformerLM

ROOT = os.path.expanduser("~/bdw-llm")
DEFAULT_CKPT = os.path.join(ROOT, "checkpoints_ft/step_0003000.pt")
TOKENIZER = os.path.join(ROOT, "tokenizer/tokenizer.json")

FMT = "<|bos|>User: {q}<|eos|><|bos|>Assistant: {a}"
# NOTE: the prompt must end at "Assistant:" with NO trailing space.
# Stage K built training examples as tok.encode("Assistant: " + answer), and
# byte-level BPE folds that space into the answer's first token (" Virgin").
# Emitting a standalone space token here puts the model in a position it never
# saw while training, which derails generation.
PROMPT_TAIL = "<|bos|>User: {q}<|eos|><|bos|>Assistant:"
MAX_PASSAGE_CHARS = 800
MIN_PARA_CHARS = 40


def parse_args():
    p = argparse.ArgumentParser(description="BDW Stage M: chat with retrieval")
    p.add_argument("question", nargs="*", help="question(s) to ask")
    p.add_argument("--ckpt", default=DEFAULT_CKPT)
    p.add_argument("--top-k", type=int, default=2, help="retrieved passages")
    p.add_argument("--max-new-tokens", type=int, default=180)
    p.add_argument("--temperature", type=float, default=0.7)
    p.add_argument("--top-k-sample", type=int, default=40)
    p.add_argument("--max-prompt-tokens", type=int, default=768)
    p.add_argument("--no-rag", action="store_true",
                   help="answer without retrieving any context")
    p.add_argument("--no-wikipedia", action="store_true")
    p.add_argument("--use-ddg", action="store_true",
                   help="also try DuckDuckGo. Off by default: from PARAM "
                        "Rudra it returned irrelevant results (TurboTax "
                        "pages for 'photosynthesis'), so Wikipedia only is "
                        "the safer default.")
    p.add_argument("--interactive", action="store_true")
    p.add_argument("--repetition-penalty", type=float, default=1.2,
                   help="divide logits of already-seen tokens by this (1.0 = off)")
    p.add_argument("--penalize-prompt", action="store_true",
                   help="also penalise tokens from the prompt/context "
                        "(off by default so RAG context can be reused)")
    p.add_argument("--loop-stop", type=int, default=8,
                   help="stop if this many tokens repeat exactly; 0 disables")
    p.add_argument("--show-prompt", action="store_true",
                   help="print the assembled prompt text before generation")
    p.add_argument("--show-specials", action="store_true",
                   help="decode the continuation with <|bos|>/<|eos|> visible")
    p.add_argument("--seed", type=int, default=1337)
    p.add_argument("--threads", type=int, default=4,
                   help="CPU threads -- the login node is shared, stay at 4")
    return p.parse_args()


# ------------------------------------------------------------------ retrieval
def fetch_wikipedia(query, top_k, tries=4):
    """Return [(title, url, paragraph)] from Wikipedia, with retries."""
    import time

    import wikipedia
    wikipedia.set_rate_limiting(True)
    out = []
    titles = []
    for attempt in range(tries):
        try:
            titles = wikipedia.search(query)
            break
        except Exception as e:
            wait = min(2 * (2 ** attempt), 30)
            print("[rag] wikipedia search attempt %d/%d failed (%s: %s) -> sleep %ds"
                  % (attempt + 1, tries, type(e).__name__, e, wait))
            time.sleep(wait)
    if not titles:
        return out
    for title in titles[:top_k * 2]:
        if len(out) >= top_k:
            break
        page = None
        for attempt in range(tries):
            try:
                page = wikipedia.page(title, auto_suggest=False, redirect=True)
                break
            except Exception as e:
                opts = getattr(e, "options", None)
                if opts:
                    try:
                        page = wikipedia.page(opts[0], auto_suggest=False, redirect=True)
                        break
                    except Exception:
                        pass
                if attempt + 1 < tries:
                    time.sleep(min(2 * (2 ** attempt), 30))
        if page is None:
            continue
        content = None
        for attempt in range(tries):
            try:
                content = page.content   # a lazy HTTP call; can fail like search()
                break
            except Exception as e:
                if attempt + 1 < tries:
                    time.sleep(min(2 * (2 ** attempt), 30))
                else:
                    print("[rag] wikipedia content failed for %r (%s: %s)"
                          % (title, type(e).__name__, e))
        if not content:
            continue
        paras = [x.strip() for x in content.split("\n")
                 if len(x.strip()) >= MIN_PARA_CHARS]
        if not paras:
            continue
        para = paras[0][:MAX_PASSAGE_CHARS]
        out.append((page.title, page.url, para))
    return out


def fetch_ddg(query, top_k):
    """Return [(title, url, snippet)] from DuckDuckGo, best effort."""
    out = []
    try:
        try:
            from duckduckgo_search import DDGS
        except Exception:
            from ddgs import DDGS
        with DDGS() as d:
            hits = list(d.text(query, max_results=top_k * 3))
    except Exception as e:
        print("[rag] duckduckgo failed: %s: %s" % (type(e).__name__, e))
        return out
    for h in hits:
        if len(out) >= top_k:
            break
        body = (h.get("body") or "").strip()
        if len(body) < MIN_PARA_CHARS:
            continue
        out.append((h.get("title") or "(no title)", h.get("href") or "", body[:MAX_PASSAGE_CHARS]))
    return out


def retrieve(query, top_k, use_wiki=True, use_ddg=False):
    passages = []
    if use_wiki:
        passages += fetch_wikipedia(query, top_k)
    if len(passages) < top_k and use_ddg:
        got = fetch_ddg(query, top_k - len(passages))
        if got:
            print("[rag] wikipedia supplied %d, duckduckgo supplied %d"
                  % (len(passages), len(got)))
        passages += got
    return passages[:top_k]


# ------------------------------------------------------------------ prompting
def build_user(question, context=""):
    """Identical to Stage K's build_user, so training and inference match."""
    ins = " ".join((question or "").split())
    ctx = " ".join((context or "").split())
    if not ctx:
        return ins
    return "%s\n\nContext:\n%s" % (ins, ctx)


def build_prompt(question, passages):
    if not passages:
        return PROMPT_TAIL.format(q=build_user(question))
    blocks = []
    for i, (title, url, para) in enumerate(passages, 1):
        src = url or title
        blocks.append("[%d] %s\n%s" % (i, src, para))
    context = "\n\n".join(blocks)
    return PROMPT_TAIL.format(q=build_user(question, context))


# ------------------------------------------------------------------ inference
@torch.no_grad()
def generate_ids(model, ids, max_new_tokens, temperature, top_k, eos_id,
                 repetition_penalty=1.2, penalize_prompt=False, loop_stop=8):
    """Greedy/sampled decode with a repetition penalty and a loop guard.

    A 28 M parameter model loops badly under pure argmax, so logits for
    tokens already emitted are divided by `repetition_penalty`. By default
    only the generated continuation is penalised -- the retrieved context
    is left alone so the model can still reuse wording from it.
    Returns (token_ids, hit_eos): hit_eos is True only when generation ended
    by emitting eos_id -- never for max_new_tokens or the loop guard.
    """
    model.eval()
    generated = []
    hit_eos = False
    for _ in range(max_new_tokens):
        idx = torch.tensor([ids], dtype=torch.long)
        idx_cond = idx[:, -model.cfg.seq_len:]
        logits, _ = model(idx_cond)
        logits = logits[0, -1].clone()
        if repetition_penalty and repetition_penalty != 1.0:
            seen = set(ids[len(ids) - len(generated):]) if not penalize_prompt else set(ids)
            if seen:
                idxs = torch.tensor(sorted(seen), dtype=torch.long)
                vals = logits[idxs]
                logits[idxs] = torch.where(
                    vals > 0, vals / repetition_penalty, vals * repetition_penalty)
        logits = logits / max(temperature, 1e-8)
        if top_k:
            v, _ = torch.topk(logits, min(top_k, logits.size(-1)))
            logits[logits < v[-1]] = -float("inf")
        probs = F.softmax(logits, dim=-1)
        nxt = int(torch.multinomial(probs, 1).item())
        if nxt == eos_id:
            hit_eos = True
            break
        ids.append(nxt)
        generated.append(nxt)
        if loop_stop and len(generated) >= 2 * loop_stop:
            if generated[-loop_stop:] == generated[-2 * loop_stop:-loop_stop]:
                break
    return ids, hit_eos


def load_model(ckpt, device):
    t0 = time.time()
    blob = torch.load(ckpt, map_location=device, weights_only=False)
    cfg = ModelConfig(**blob["model_config"])
    model = TransformerLM(cfg).to(device)
    model.load_state_dict(blob["model"])
    model.eval()
    print("[model] %s" % ckpt)
    print("[model] step=%s saved_at=%s stage=%s" % (
        blob.get("step"), blob.get("saved_at"), blob.get("stage")))
    print("[model] vocab=%d seq_len=%d d_model=%d layers=%d params=%d" % (
        cfg.vocab_size, cfg.seq_len, cfg.d_model, cfg.n_layers, model.num_params()))
    print("[model] loaded in %.1fs on %s" % (time.time() - t0, device))
    return model, blob


def ask(model, tok, bos, eos, question, args, use_rag=True):
    torch.manual_seed(args.seed)
    random.seed(args.seed)

    passages = []
    if use_rag:
        t0 = time.time()
        passages = retrieve(question, args.top_k,
                            use_wiki=not args.no_wikipedia,
                            use_ddg=args.use_ddg)
        print("[rag] retrieved %d passage(s) in %.2fs" % (len(passages), time.time() - t0))

    prompt = build_prompt(question, passages)
    ids = tok.encode(prompt, add_special_tokens=False).ids
    # keep room for generation
    budget = args.max_prompt_tokens
    trimmed = False
    if len(ids) > budget:
        ids = ids[-budget:]
        trimmed = True
    print("[prompt] %d token ids%s  head=%s  tail=%s"
          % (len(ids), " (prompt trimmed to last %d)" % budget if trimmed else "",
             ids[:5], ids[-5:]))
    if ids[:1] != [bos]:
        print("[warn] prompt does not start with <|bos|>")

    t0 = time.time()
    out_ids, hit_eos = generate_ids(model, list(ids), args.max_new_tokens,
                                    args.temperature, args.top_k_sample, eos,
                                    repetition_penalty=args.repetition_penalty,
                                    penalize_prompt=args.penalize_prompt,
                                    loop_stop=args.loop_stop)
    dt = time.time() - t0
    new_ids = out_ids[len(ids):]
    text = tok.decode(new_ids, skip_special_tokens=True)
    print("[gen] %d new tokens in %.1fs (%.1f tok/s)  hit_eos=%s"
          % (len(new_ids), dt, len(new_ids) / max(dt, 1e-9),
             hit_eos))
    if args.show_specials:
        print("[gen] raw ids  : %s" % new_ids)
        print("[gen] raw text : %r" % tok.decode(new_ids, skip_special_tokens=False))
    if args.show_prompt:
        print("[prompt] text  :\n%s" % tok.decode(ids, skip_special_tokens=False))
    return text.strip(), passages, prompt, len(new_ids), dt


def show_passages(passages):
    if not passages:
        print("  (no external context)")
        return
    for i, (title, url, para) in enumerate(passages, 1):
        print("  [%d] %s" % (i, title))
        print("      %s" % (url or "(no url)"))
        print("      %s" % para[:240].replace("\n", " "))


def main():
    args = parse_args()
    torch.set_num_threads(args.threads)

    tok = Tokenizer.from_file(TOKENIZER)
    bos = tok.token_to_id("<|bos|>")
    eos = tok.token_to_id("<|eos|>")
    pad = tok.token_to_id("<|pad|>")
    print("tokenizer    : %s" % TOKENIZER)
    print("special ids  : pad=%d bos=%d eos=%d vocab=%d" % (pad, bos, eos,
                                                            tok.get_vocab_size()))

    if not os.path.exists(args.ckpt):
        raise SystemExit("checkpoint missing: %s" % args.ckpt)
    model, _blob = load_model(args.ckpt, "cpu")

    use_rag = not args.no_rag
    print("rag          : %s" % ("ON (top %d)" % args.top_k if use_rag else "OFF"))
    print()

    questions = list(args.question)
    if args.interactive or not questions:
        if not args.interactive and not questions:
            print("(no question given; entering --interactive mode)")
        print("Type a question, or 'quit' / 'exit' to stop.\n")
        while True:
            try:
                q = input("You> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if not q or q.lower() in ("quit", "exit", "q"):
                break
            run_one(model, tok, bos, eos, q, args, use_rag)
        return

    for q in questions:
        run_one(model, tok, bos, eos, q, args, use_rag)


def run_one(model, tok, bos, eos, question, args, use_rag):
    t0 = time.time()
    answer, passages, prompt, n_new, gen_s = ask(model, tok, bos, eos, question,
                                                 args, use_rag)
    print("=" * 70)
    print("QUESTION")
    print("=" * 70)
    print(question)
    print()
    print("RETRIEVED CONTEXT")
    show_passages(passages)
    print()
    print("ANSWER")
    print("=" * 70)
    print(answer if answer else "(empty -- the model produced no text before eos)")
    print()
    print("-" * 70)
    print("total %.1fs  |  retrieved %d  |  new tokens %d  |  seed %d"
          % (time.time() - t0, len(passages), n_new, args.seed))
    print("-" * 70)
    print()


if __name__ == "__main__":
    main()
