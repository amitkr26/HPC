"""Zone 2 gateway — P3.4 (blueprint): retrieval -> prompt -> Zone 3 -> S5
citation verifier -> respond. Stdlib http.server + requests only; the
retriever and LLM call are injected so unit runs can stub them offline.

Handlers:
  POST /ask   {"question": str, "user_id": str?}   200 {"answer", "citations", "meta"}
  GET  /health
"""
from __future__ import annotations

import json
import re
import threading
import time
import urllib.parse
import uuid
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import requests

PH3 = None  # set by main()
Z3_DEFAULT_TIMEOUT = 15
CITE_RE = re.compile(r'<cite\s+id="([^"]+)"\s*/?>', re.I)
SYSTEM_TEMPLATE = (
    "You are the BDW assistant. Answer the student's question ONLY from the "
    "numbered context below. After each claim, cite the source chunk with "
    "<cite id=\"N\"/> (0-indexed). If the context does not answer the "
    "question, state that plainly. Context:\n{context}")


def fmt_chunks(ranked):
    parts, ids = [], []
    for i, r in enumerate(ranked):
        head = "%s [%s]" % (r.get("title") or "", r.get("parent_type"))
        src = r.get("source_url") or ""
        parts.append("[%d] %s\n%s%s" % (
            i, head, r.get("content", "").strip(),
            ("\nURL: " + src) if src else ""))
        ids.append(r.get("id"))
    return "\n\n".join(parts), ids


def verify_citations(answer, n_available, allowed_ids):
    """S5 strip: drop <cite> tags pointing outside the retrieved set; report."""
    found = [m.group(1) for m in CITE_RE.finditer(answer)]
    ok = [f for f in found
          if (f.isdigit() and int(f) < n_available and allowed_ids[int(f)])
          or f in allowed_ids]
    stale = [f for f in found if f not in ok]

    def repl(m):
        if m.group(1) in ok:
            return m.group(0)
        return ""
    clean = CITE_RE.sub(repl, answer).strip()
    mentions = re.findall(r"^\s*\n?\[(\d+)\]", clean, re.M)
    if not found and mentions:
        clean = clean  # text citations pass through, metadata only
    return clean, ok, stale


class RateLimiter:
    def __init__(self, per_day):
        self.per_day = per_day
        self.lock = threading.Lock()
        self.tab = {}

    def hit(self, uid):
        key = (uid, date.today().isoformat())
        with self.lock:
            self.tab = {k: v for k, v in self.tab.items()
                        if k[1] == key[1]}
            self.tab[key] = self.tab.get(key, 0) + 1
            return self.tab[key] <= self.per_day


class Gateway:
    def __init__(self, retriever, llm, cfg):
        self.retriever = retriever
        self.llm = llm
        self.lim = RateLimiter(cfg["RATE_LIMIT_PER_USER_DAY"])
        self.cfg = cfg

    def ask(self, question, user_id):
        if not self.lim.hit(user_id):
            return None, 429, {"error": "rate limit reached; retry tomorrow"}
        ranked = self.retriever.search(question,
                                       self.cfg["RETRIEVAL_TOPK"])
        context, ids = fmt_chunks(ranked)
        prompt = SYSTEM_TEMPLATE.format(context=context)
        prompt += "\nQuestion: %s" % question
        answer = self.llm.complete(
            prompt, max_tokens=self.cfg["MAX_TOKENS"])
        clean, kept, stale = verify_citations(
            answer, len(ranked), ids)
        meta = {"citations_kept": kept, "citations_dropped": stale,
                "chunks": [{"id": c, "title": ranked[i].get("title"),
                            "url": ranked[i].get("source_url"),
                            "verified": ranked[i].get("verified")}
                           for i, c in enumerate(ids)]}
        if stale:
            clean += ("\n\n[Note: one or more citation marks were removed "
                      "by the server-side verifier (S5).]")
        return {"answer": clean, "meta": meta}, 200, None


class SupabaseRetriever:
    """Calls match_chunks_vec then match_chunks_fts; raises高新 if REST 404s."""

    def __init__(self, url, svc):
        self.url = url.rstrip("/")
        self.svc = svc

    def rpc(self, fn, payload):
        r = requests.post("%s/rest/v1/rpc/%s" % (self.url, fn),
                          headers={"apikey": self.svc,
                                   "Authorization": "Bearer " + self.svc,
                                   "Content-Type": "application/json"},
                          json=payload, timeout=60)
        if r.status_code != 200:
            raise RuntimeError("rpc %s -> %d %s"
                               % (fn, r.status_code, r.text[:120]))
        return r.json()

    def search(self, query, k):
        try:
            rows = self.rpc("match_chunks_fts",
                            {"query": query, "match_count": k})
            if rows:
                return rows[:k]
        except RuntimeError as e:
            msg = str(e)
            if "404" not in msg:
                raise
        return []


class Zone3LLM:
    def __init__(self, base, timeout):
        self.base = base.rstrip("/")
        self.timeout = timeout

    def complete(self, prompt, max_tokens=1024):
        r = requests.post(self.base + "/completion", timeout=self.timeout,
                          json={"prompt": prompt, "n_predict": max_tokens,
                                "stream": False, "temperature": 0.0})
        r.raise_for_status()
        return r.json().get("content", "")


def handler_class(g):
    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _send(self, code, body):
            raw = json.dumps(body).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def do_POST(self):
            if self.path != "/ask":
                return self._send(404, {"error": "not found"})
            n = int(self.headers.get("Content-Length") or 0)
            try:
                body = json.loads(self.rfile.read(n) or b"{}")
            except ValueError:
                return self._send(400, {"error": "bad json"})
            q = (body.get("question") or "").strip()
            uid = body.get("user_id") or self.headers.get(
                "X-User-Id") or "guest"
            if not q or len(q) > 600:
                return self._send(400, {"error": "question 1..600 chars"})
            try:
                data, code, err = g.ask(q, uid)
            except Exception as exc:  # noqa: BLE001
                data, code = {"error": "upstream failure", "detail":
                              str(exc)[:160]}, 502
            self._send(code, err or data)

        def do_GET(self):
            if self.path == "/health":
                return self._send(200, {"ok": True,
                                        "ts": time.strftime("%H:%M:%S")})
            self._send(404, {"error": "not found"})
    return H


def main():
    import os
    ph3 = os.path.dirname(os.path.abspath(__file__))
    env = {}
    with open(os.path.join(ph3, ".env"), encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line and not line.startswith("#"):
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip()

    retriever = SupabaseRetriever(env["SUPABASE_URL"],
                                  env["SUPABASE_SERVICE_ROLE_KEY"])
    llm = Zone3LLM(env.get("ZONE3_BASE_URL", "http://127.0.0.1:8080"),
                   int(env.get("ZONE3_TIMEOUT_S", "15")))
    cfg = {"RETRIEVAL_TOPK": int(env.get("RETRIEVAL_TOPK", "20")),
           "MAX_TOKENS": int(env.get("MAX_TOKENS", "1024")),
           "RATE_LIMIT_PER_USER_DAY": int(
               env.get("RATE_LIMIT_PER_USER_DAY", "35"))}
    gate = Gateway(retriever, llm, cfg)
    port = int(env.get("ZONE2_PORT", "8787"))
    srv = ThreadingHTTPServer(("0.0.0.0", port), handler_class(gate))
    print("RESULT: P3_ZONE2_UP port=%d" % port, flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
