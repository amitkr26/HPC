"""P2.5: append-only data patch -> data/bdw_sft_v2.jsonl.

Motivation (errata 15.2 / 15.3):
  * R5 refusal style bled into benign prompts (ge_02 answered with the
    refusal script) -> r6 counter-examples: benign work/study/email
    questions answered on-task, while every R5 topic keeps its refusal.
  * Citations on unseen rows were structurally unresolvable -- the id is
    never in the prompt, and val row ids are never trained on (all four
    post-SFT cites were memorised train-id prefixes + invented tails) ->
    r2b rows: the gated r2 answer with "(Ref: <row_id>)" appended to the
    QUESTION, teaching copy-from-context. Eval suite p2-v2 presents the
    same format, and base + SFT are both re-scored on it.

Guarantees:
  * original bdw_sft.jsonl bytes are preserved verbatim (binary append),
    so P2.1 evidence and its md5 stay valid
  * NO new val rows: every added row is forced split="train" -> the
    579-row val set, val-loss curve and the frozen eval suite (built from
    val rows only) are unchanged
  * every added row passes the P2.1 gate (r2b answers are the identical
    already-gated r2 answers; r6 is synthetic and gate-checked)

RESULT: P25_DATA_OK ...  /  RESULT: P25_DATA_FAIL ...
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import traceback

SRC = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SRC)
import bdw_build_sft as B  # noqa: E402

ROOT = os.path.expanduser("~/bdw-llm")
IN_JSONL = os.path.join(ROOT, "data/bdw_sft.jsonl")
OUT_JSONL = os.path.join(ROOT, "data/bdw_sft_v2.jsonl")
TOK_PATH = os.path.join(ROOT, "teacher_model_7b")
MAX_TOKENS = 1024

# Benign prompts deliberately outside the R5 topic list (no medical/legal/
# finance/... scope topics, no weather/translate/pizza, none of the four
# GeneralEnglish suite constants). Answers: direct, on-task, >=5 words,
# ENDSENT-terminated, no refusal/meta-refusal markers.
R6 = [
    ("Draft a short email apologising for submitting my assignment late.",
     "Dear Professor, I am writing to apologise for submitting the assignment "
     "past the deadline. The delay was due to an unforeseen personal "
     "commitment, and I have attached the completed work for your review. I "
     "will ensure this does not happen again. Regards, [Your Name]."),
    ("Write a polite email asking a professor for a recommendation letter.",
     "Dear Professor, I hope you are doing well. I was a student in your "
     "course last semester and I am applying for graduate programmes now. I "
     "would be grateful if you could write a recommendation letter for me. I "
     "have attached my resume and the deadlines for your reference. Thank you "
     "very much for your time and support."),
    ("Reply to a client thanking them for their feedback on the first draft.",
     "Dear Client, thank you for taking the time to share detailed feedback "
     "on the first draft. I have noted your comments and will incorporate "
     "them in the next revision. Please let me know if anything else needs "
     "attention. I appreciate your guidance and look forward to your review."),
    ("Write a short thank-you message to send after a job interview.",
     "Dear Hiring Manager, thank you for the opportunity to interview for the "
     "position yesterday. I enjoyed learning about the team and the role, and "
     "our conversation confirmed my interest in contributing to your "
     "projects. Please feel free to reach out if you need any further "
     "information. I look forward to hearing from you."),
    ("Write an email to HR requesting a copy of my offer letter.",
     "Dear HR Team, I hope this message finds you well. Could you please "
     "share a soft copy of my offer letter for my personal records? It would "
     "be helpful for my documentation and future reference. Thank you for "
     "your assistance, and please let me know if you need anything from my "
     "side."),
    ("Politely decline a birthday party invitation from a friend.",
     "Dear Friend, thank you so much for inviting me to your birthday "
     "celebration. Unfortunately I will not be able to attend due to a prior "
     "commitment on that day. I am wishing you a wonderful evening with your "
     "loved ones, and I will catch up with you very soon. Have a great "
     "party!"),
    ("Ask a colleague to review your code before the release.",
     "Hi, could you please take a look at my changes before the release "
     "tomorrow? I have updated the module and added tests for the new "
     "behaviour. Your review comments on correctness and readability would be "
     "really helpful. I am happy to walk through the diff if that is easier. "
     "Thanks a lot!"),
    ("Write an email asking your mentor for a deadline extension on a "
     "project.",
     "Dear Mentor, I am writing to request a short extension on the project "
     "deadline. Due to competing deliverables this week, I need a few extra "
     "days to complete the work properly. I have already finished most of "
     "the analysis and will share the remaining sections soon. Thank you for "
     "considering my request."),
    ("Congratulate a friend who just cleared their technical interview.",
     "Congratulations on clearing your technical interview! Your preparation "
     "and hard work have really paid off, and this offer is well deserved. I "
     "am sure you will do great things in the new role. Let us celebrate "
     "together this weekend, and do keep me posted on the joining details. "
     "Cheers!"),
    ("Write an email proposing two time slots for a meeting.",
     "Hi, I would like to schedule a quick sync to discuss the pending items. "
     "Would Tuesday morning or Wednesday afternoon work for you? Please "
     "reply with the slot that suits your calendar, and I will send an "
     "invite accordingly. Looking forward to meeting you."),
    ("Which planet in our solar system has the most moons?",
     "Saturn currently has the highest number of confirmed moons of any "
     "planet in our solar system, surpassing Jupiter after recent "
     "discoveries. Many of these moons are small irregular bodies captured "
     "by the planet's gravity. Both gas giants will likely keep collecting "
     "new candidates as surveys improve."),
    ("Why does the sky appear blue during the day?",
     "Sunlight is scattered by the gases in the atmosphere, and the shorter "
     "blue wavelengths scatter much more strongly than the longer red "
     "wavelengths. This scattered blue light reaches our eyes from every "
     "direction, which is why the sky looks blue. At sunset the light "
     "travels through more atmosphere, so the reds dominate."),
    ("Who wrote the play Romeo and Juliet?",
     "Romeo and Juliet was written by William Shakespeare, the English "
     "playwright and poet of the late sixteenth and early seventeenth "
     "centuries. The tragedy is set in Verona and has become one of the most "
     "frequently staged and adapted works in world literature. It is widely "
     "studied in schools across the world."),
    ("What is the capital of Australia?",
     "The capital of Australia is Canberra, a planned city located between "
     "Sydney and Melbourne in the Australian Capital Territory. While Sydney "
     "and Melbourne are larger and more famous, Canberra has served as the "
     "seat of the national government since the country federated. The "
     "Parliament House and many national institutions are located there."),
    ("Explain the difference between a laptop and a desktop computer in two "
     "sentences.",
     "A laptop is a portable all-in-one computer with a built-in battery, "
     "screen and keyboard, designed for work on the move. A desktop is a "
     "stationary machine that usually offers more upgradeable parts, better "
     "cooling and stronger performance for the same budget."),
    ("How should I prepare for a technical interview in VLSI?",
     "Revise digital logic, CMOS fundamentals and the RTL design flow "
     "first, then practise standard interview questions on your projects. Be "
     "ready to explain your resume in depth, including any RTL, "
     "verification or physical design work you have done. Mock interviews "
     "with a friend will also sharpen your communication under pressure."),
    ("Give me tips to make my resume stand out.",
     "Start with a clear summary that matches the role, then list "
     "achievements with measurable impact instead of plain job duties. Keep "
     "the layout simple, use consistent formatting, and tailor the keywords "
     "for each application. Proofread carefully, since small typos can cost "
     "an interview call."),
    ("What is a good way to take notes during a lecture?",
     "Use a structured method such as the Cornell style, where you write "
     "main ideas on the right and cue questions on the left, then summarise "
     "after class. Keep notes short and in your own words so you engage with "
     "the material instead of copying slides. Review them within a day to "
     "move the content into long-term memory."),
    ("How do I break a big project into smaller tasks?",
     "List the final deliverables first, then split each one into "
     "milestones that can be finished within a few days. Order the "
     "milestones by dependency and effort so the critical path is clear, "
     "and track them on a simple board with clear owners. Review progress "
     "weekly and adjust the plan when something slips."),
    ("Suggest a weekly study schedule for an engineering student.",
     "Plan focused morning blocks for difficult subjects, keep afternoons "
     "for labs and problem sets, and reserve evenings for revision and "
     "short practice tests. Leave one evening free for rest so you do not "
     "burn out, and protect weekends for catching up on backlog. Adjust the "
     "timetable each week based on upcoming exams."),
    ("What should I include in the opening of a cover letter?",
     "Open with the specific role you are applying for and a strong line "
     "about why this company interests you. Mention a concrete achievement "
     "that relates to the role so the hiring manager sees immediate value. "
     "Keep the opening short so the reader continues to the rest of the "
     "letter."),
    ("How do I follow up after an interview without sounding pushy?",
     "Wait a few working days, then send a short thank-you note that "
     "repeats your interest and adds one detail from the discussion. Ask "
     "gently about the next steps and timelines rather than demanding a "
     "decision. Keep the tone warm and professional, and avoid sending more "
     "than one follow-up before the promised date."),
    ("What is the best way to answer tell me about yourself?",
     "Give a short professional summary that starts with your current role, "
     "highlights two relevant achievements, and connects them to the "
     "position you are seeking. Keep it under a minute and avoid personal "
     "details that are not relevant to the job. Practise the answer aloud "
     "so it sounds natural and confident."),
    ("How can I improve my LinkedIn profile?",
     "Use a clear professional photo and a headline that states your "
     "specialty rather than just your job title. Fill the about section "
     "with a short story of your skills and goals, and list projects or "
     "certifications that prove them. Engage with posts in your field so "
     "recruiters notice your activity as well."),
    ("Summarise this in one sentence: The city council approved the new "
     "park after a long debate and the residents celebrated.",
     "The city council approved the new park following a lengthy debate, "
     "and the residents celebrated the decision."),
    ("Write a short farewell speech for a college farewell function.",
     "Dear friends and teachers, today we close one chapter and begin "
     "another. I thank every professor who shaped our thinking and every "
     "friend who made the journey memorable. May we carry these lessons "
     "into our careers and stay in touch for years to come. Wishing everyone "
     "success and happiness ahead!"),
    ("Improve this sentence: We are doing the needful, kindly revert.",
     "Here is a clearer version: We have taken care of the required steps "
     "and will await your confirmation. The revised wording is direct, "
     "professional and free of outdated business phrases, which makes the "
     "message easier for any reader to understand quickly."),
    ("Write a short polite note declining a dinner invitation.",
     "Dear Host, thank you for inviting me to dinner. I am unable to attend "
     "on that evening because of a family commitment, but I truly "
     "appreciate the kind thought. I would love to join next time, and I "
     "hope you have a lovely evening with everyone."),
    ("Suggest three subject lines for an email about a campus recruitment "
     "drive.",
     "Here are a few options: Campus recruitment drive registrations open; "
     "Join the campus drive and book your slot; Registrations are open for "
     "the campus placement drive. Pick the one that matches your audience, "
     "keep the wording short, and add the last date in the body of the "
     "email rather than the subject."),
    ("Explain what a resume summary is in two sentences.",
     "A resume summary is a short paragraph at the top of your resume that "
     "highlights your experience, skills and biggest achievements. It gives "
     "the recruiter a quick reason to keep reading the rest of your "
     "profile."),
]


def build_candidates(rows, stats):
    """Derive r2b (train-only) + r6 candidates from parsed v1 rows."""
    cands = []
    for row in rows:
        if row.get("source") != "r2" or row.get("split") != "train":
            continue
        rid = str(row.get("row_id", ""))
        if not rid:
            stats["drop"]["r2b_no_rid"] = stats["drop"].get(
                "r2b_no_rid", 0) + 1
            continue
        q = row["messages"][0]["content"]
        a = row["messages"][1]["content"]
        nq = "%s (Ref: %s)" % (q, rid)
        c = B.rec("r2b", nq, a, table=row.get("table", ""), row_id=rid)
        cands.append(c)
        stats["made"]["r2b"] = stats["made"].get("r2b", 0) + 1
    for q, a in R6:
        for qv in B.R5_QVAR:
            c = B.rec("r6", qv.format(q=q), a)
            cands.append(c)
            stats["made"]["r6"] = stats["made"].get("r6", 0) + 1
    return cands


def tokenize_new(cands, stats, tokenizer):
    final = []
    for c in cands:
        text = tokenizer.apply_chat_template(
            [{"role": "user", "content": c["question"]},
             {"role": "assistant", "content": c["response"]}],
            tokenize=False, add_generation_prompt=False)
        n = len(tokenizer(text, add_special_tokens=False)["input_ids"])
        if n > MAX_TOKENS:
            stats["drop"]["long"] = stats["drop"].get("long", 0) + 1
            continue
        c["tokens"] = n
        final.append(c)
    return final


def row_of(c):
    row = {"id": c["qid"],
           "messages": [{"role": "user", "content": c["question"]},
                        {"role": "assistant", "content": c["response"]}],
           "source": c["source"], "split": "train"}
    for k in ("table", "row_id", "tokens"):
        if k in c:
            row[k] = c[k]
    return row


def self_test():
    """Synthetic rows: no cluster data needed; asserts the patch rules."""
    import re as _re
    synth = [
        {"id": "aaaa", "source": "r2", "split": "train",
         "table": "opportunities", "row_id": "RID-TRAIN",
         "messages": [{"role": "user", "content":
                       "Am I eligible for the X position at Y?"},
                      {"role": "assistant", "content":
                       "You are eligible (Ref: RID-TRAIN)."}]},
        {"id": "bbbb", "source": "r2", "split": "val",
         "table": "opportunities", "row_id": "RID-VAL",
         "messages": [{"role": "user", "content":
                       "Am I eligible for the V position at Z?"},
                      {"role": "assistant", "content":
                       "You are eligible (Ref: RID-VAL)."}]},
        {"id": "cccc", "source": "r5", "split": "train",
         "messages": [{"role": "user", "content":
                       "Can you diagnose my skin rash from this photo?"},
                      {"role": "assistant", "content":
                       "I can't help with medical questions -- "
                       "BerojgarDegreeWala focuses on jobs."}]},
    ]
    stats = {"made": {}, "drop": {}}
    cands = build_candidates(synth, stats)
    r2b = [c for c in cands if c["source"] == "r2b"]
    r6 = [c for c in cands if c["source"] == "r6"]
    assert len(r2b) == 1, "r2b must come from TRAIN r2 rows only: %d" % len(r2b)
    assert "(Ref: RID-TRAIN)" in r2b[0]["question"], "r2b prompt suffix"
    assert r2b[0]["response"] == synth[0]["messages"][1]["content"], \
        "r2b answer must be the identical gated r2 answer"
    assert all("RID-VAL" not in c["question"] for c in r2b), \
        "val rows must never be mirrored"
    assert len(r6) == len(R6) * len(B.R5_QVAR), "r6 row count"
    assert len({c["qid"] for c in cands}) == len(cands), "qid uniqueness"
    ge = set()
    # the four frozen GeneralEnglish suite constants must never be trained on
    import p2_baseline as PB
    ge.update(PB.GENERAL)
    assert not (ge & {c["question"] for c in r6}), \
        "r6 collides with a GeneralEnglish suite prompt"
    for c in r6:
        a = c["response"]
        assert len(a.split()) >= 5, "short answer: %r" % a[:40]
        assert a.rstrip().endswith(B.ENDSENT), "ENDSENT: %r" % a[-20:]
        assert not B.REFUSAL_RE.match(a), "refusal start: %r" % a[:40]
        assert not B.REF_MARK_RE.search(a), "refusal marker: %r" % a[:40]
        assert not B.META_REF_RE.search(a), "meta ref: %r" % a[:40]
        assert not _re.search(r"\bHuman\s*:|\bAssistant\s*:",
                              c["question"] + " " + a), "role leak"
        reason = B.gate(c, stats, fidelity_text=None)
        assert reason is None, "gate(%s)=%s" % (c["qid"], reason)
    reason = B.gate(r2b[0], stats, fidelity_text=None)
    assert reason is None, "r2b gate=%s" % reason
    r5 = synth[2]                       # r5 rows keep working unchanged
    reason = B.gate({"question": r5["messages"][0]["content"],
                     "response": r5["messages"][1]["content"],
                     "source": r5["source"]}, stats)
    assert reason is None, "r5 gate=%s" % reason
    print("self-test OK: r2b=1 r6=%d (all gates clean, no GE collision, "
          "val rows untouched)" % len(r6))
    print("RESULT: P25_DATA_OK mode=self_test r6=%d" % len(r6))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--no-tokens", action="store_true",
                    help="skip the Qwen token-length gate (logic checks only;"
                         " a training file MUST carry tokens)")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return

    raw = open(IN_JSONL, "rb").read()
    if not raw.endswith(b"\n"):
        raw += b"\n"
    lines = raw.split(b"\n")[:-1]
    rows = [json.loads(x) for x in lines]
    orig_n = len(rows)
    orig_val = sum(1 for r in rows if r.get("split") == "val")
    orig_train = sum(1 for r in rows if r.get("split") == "train")
    print("input      : %s (%d rows, train=%d val=%d)"
          % (IN_JSONL, orig_n, orig_train, orig_val))

    stats = {"made": {}, "drop": {}}
    cands = build_candidates(rows, stats)
    seen = {r["id"] for r in rows}
    gated = []
    for c in cands:
        if c["qid"] in seen:
            stats["drop"]["dup"] = stats["drop"].get("dup", 0) + 1
            continue
        reason = B.gate(c, stats, fidelity_text=None)
        if reason:
            stats["drop"][reason] = stats["drop"].get(reason, 0) + 1
            continue
        seen.add(c["qid"])
        gated.append(c)
    print("gated      : %d candidates -> %d kept, drops=%s"
          % (len(cands), len(gated), stats["drop"] or "none"))

    tokenizer = None
    if not args.no_tokens:
        from transformers import AutoTokenizer
        tokenizer = AutoTokenizer.from_pretrained(TOK_PATH,
                                                  local_files_only=True)
        gated = tokenize_new(gated, stats, tokenizer)
        print("tokens     : %d rows passed the <=%d-token gate (drops=%d)"
              % (len(gated), MAX_TOKENS, stats["drop"].get("long", 0)))

    n2b = sum(1 for c in gated if c["source"] == "r2b")
    n6 = sum(1 for c in gated if c["source"] == "r6")
    out_lines = [row_of(c) for c in gated]
    assert all(r["split"] == "train" for r in out_lines), "new val row!"

    tmp = OUT_JSONL + ".tmp"
    with open(tmp, "wb") as fh:
        fh.write(raw)                                  # v1 bytes verbatim
        for r in out_lines:
            fh.write((json.dumps(r, ensure_ascii=False) + "\n").encode("utf-8"))
    os.replace(tmp, OUT_JSONL)
    md5 = hashlib.md5(open(OUT_JSONL, "rb").read()).hexdigest()
    size = os.path.getsize(OUT_JSONL)

    lens = [c["tokens"] for c in gated if "tokens" in c]
    print("output     : %s" % OUT_JSONL)
    print("added      : r2b=%d r6=%d total=%d (all split=train)"
          % (n2b, n6, len(out_lines)))
    print("val        : %d (unchanged -- no new val rows)" % orig_val)
    print("tokens     : %s" % ({"min": min(lens), "med": sorted(lens)[
        len(lens) // 2], "max": max(lens), "sum": sum(lens)} if lens else {}))
    print("md5        : %s (%d bytes)" % (md5, size))
    train_total = orig_train + len(out_lines)
    print("train      : %d -> %d  (2 epochs = 2*ceil(%d/32) = %d steps)"
          % (orig_train, train_total, train_total,
             2 * -(-train_total // 32)))
    if n6 < 100 or n2b < 100:
        print("RESULT: P25_DATA_FAIL too_few r2b=%d r6=%d" % (n2b, n6))
        sys.exit(1)
    print("RESULT: P25_DATA_OK orig=%d train=%d val=%d added_r2b=%d "
          "added_r6=%d new_train=%d md5=%s"
          % (orig_n, orig_train, orig_val, n2b, n6, train_total, md5))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        print("RESULT: P25_DATA_FAIL %s" % sys.exc_info()[1], flush=True)
        sys.exit(1)
