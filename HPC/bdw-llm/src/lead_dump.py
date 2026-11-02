import glob
import json
import os

TITLES = {
    "Bayes' theorem", "Eigenvalues and eigenvectors", "Derivative",
    "Laplace transform", "Numerical analysis",
    "Flip-flop (electronics)", "Static timing analysis",
    "Metastability (electronics)", "Verilog",
    "I2C", "Interrupt", "Watchdog timer", "Direct memory access",
    "Real-time operating system",
    "Analysis of algorithms", "Concurrent computing", "Operating system",
    "Compiler", "Internet protocol suite",
    "Backpropagation", "Attention (machine learning)", "Overfitting",
    "Stochastic gradient descent", "Convolutional neural network",
}

paths = ["data/raw/vlsi_wikipedia.json"] + sorted(
    glob.glob("data/raw/p4_*_contexts.json"))
want = set(TITLES)
for path in paths:
    if not os.path.isfile(path):
        continue
    with open(path, encoding="utf-8") as fh:
        doc = json.load(fh)
    for ch in doc.get("chunks", []):
        t = ch.get("title")
        if t in want:
            txt = " ".join((ch.get("text") or "").split())
            print("## %s :: %s" % (t, txt[:430]))
            want.discard(t)
print("MISSING:", sorted(want))
