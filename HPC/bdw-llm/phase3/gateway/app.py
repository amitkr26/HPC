"""Zone 2 gateway - P3.4 (blueprint): retrieval -> prompt -> Zone 3 -> S5
citation verifier -> respond. Stdlib http.server + requests only; the
retriever, LLM call and web-search client are injected so unit runs can
stub them offline.

Handlers:
  POST /ask   {"question": str, "user_id": str?, "web": "auto"|"on"|"off"?}
              200 {"answer", "citations", "meta"}
  GET  /health

Web-RAG routing: when the question smells fresh (deadlines, news, dates)
or local retrieval comes back weak, the router escalates to a search API
(Tavily/Serper placeholder). Snippets are shaped exactly like bdw_chunks
rows - id=uuid5(url), verified=False, parent_type="web" - and appended
after local chunks, so fmt_chunks, the citation allowlist and the S5
verifier work unchanged. No key configured -> web is disabled and /ask
behaves exactly as before.
"""
from __future__ import annotations

import json
import os
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
FRESH_RE = re.compile(
    r"\b(latest|current|today|recent\w*|news|now|202[5-9]|deadlines?|"
    r"announce\w*|openings?|admissions?|results?)\b", re.I)
SYSTEM_TEMPLATE = (
    "You are the BDW assistant. Answer the student's question ONLY from the "
    "numbered context below. Earlier conversation turns (if present) are "
    "background you may refer to, but every NEW claim must be grounded in "
    "the context and cited. After each claim, cite the source chunk with "
    "<cite id=\"N\"/> (0-indexed). If the context does not answer the "
    "question, state that plainly. Context:\n{context}")
WEB_PREAMBLE = (
    "\n\nSources marked [web] are live internet results fetched for this "
    "question. They are supplementary to the course database, may change "
    "over time, and were not verified by BDW. Cite them with the same "
    "<cite id=\"N\"/> form when you use them.")
HISTORY_TURNS = 12
HISTORY_CHAR_CAP = 1500
CONV_HEADER = "\n\nConversation so far:"


def _clean(text, cap):
    out = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", " ", str(text or ""))
    out = re.sub(r"[ \t]+", " ", out).strip()
    return out[:cap]


def should_web(question, n_local, mode):
    """Pure router: returns (use_web, reason). mode in auto|on|off."""
    if mode == "off":
        return False, "forced-off"
    if mode == "on":
        return True, "forced-on"
    if FRESH_RE.search(question):
        return True, "freshness"
    if n_local == 0:
        return True, "weak-local"
    return False, "local-sufficient"


def build_ask_prompt(context, history, question, web_used=False):
    """Gateway-side single source of truth for the /ask prompt: context
    (+ web preamble), then the threaded conversation, then the question.
    History entries are filtered to role in user|assistant, capped to the
    last HISTORY_TURNS turns and HISTORY_CHAR_CAP chars per turn."""
    prompt = SYSTEM_TEMPLATE.format(context=context)
    if web_used:
        prompt += WEB_PREAMBLE
    turns = [h for h in (history or [])
             if isinstance(h, dict)
             and h.get("role") in ("user", "assistant")
             and isinstance(h.get("content"), str)
             and h["content"].strip()]
    turns = turns[-HISTORY_TURNS:]
    if turns:
        lines = [CONV_HEADER]
        for h in turns:
            lines.append("%s: %s" % (h["role"].capitalize(),
                                     h["content"].strip()[:HISTORY_CHAR_CAP]))
        prompt += "\n".join(lines)
    prompt += "\nQuestion: %s" % question
    return prompt, len(turns)


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
    def __init__(self, retriever, llm, cfg, web=None):
        self.retriever = retriever
        self.llm = llm
        self.web = web
        self.lim = RateLimiter(cfg["RATE_LIMIT_PER_USER_DAY"])
        self.cfg = cfg

    def ask(self, question, user_id, web_mode=None, history=None):
        if not self.lim.hit(user_id):
            return None, 429, {"error": "rate limit reached; retry tomorrow"}
        mode = web_mode or self.cfg.get("WEB_RAG_MODE", "auto")
        ranked = self.retriever.search(question,
                                       self.cfg["RETRIEVAL_TOPK"])
        use_web, reason = should_web(question, len(ranked), mode)
        web_used = False
        if use_web and self.web is not None:
            try:
                web_rows = self.web.search(
                    question, int(self.cfg.get("WEB_TOPK", 5)))
            except Exception:  # noqa: BLE001
                web_rows, reason = [], "web-error"
            if web_rows:
                have = {r.get("id") for r in ranked}
                for w in web_rows:
                    if w.get("id") not in have:
                        ranked.append(w)
                web_used = True
        context, ids = fmt_chunks(ranked)
        prompt, n_turns = build_ask_prompt(context, history, question,
                                           web_used)
        answer = self.llm.complete(
            prompt, max_tokens=self.cfg["MAX_TOKENS"])
        clean, kept, stale = verify_citations(
            answer, len(ranked), ids)
        meta = {"routing": {"mode": mode, "web_used": web_used,
                            "reason": reason, "history_turns": n_turns},
                "citations_kept": kept, "citations_dropped": stale,
                "chunks": [{"id": c, "title": ranked[i].get("title"),
                            "url": ranked[i].get("source_url"),
                            "verified": ranked[i].get("verified"),
                            "source": ranked[i].get("parent_type")}
                           for i, c in enumerate(ids)]}
        if stale:
            clean += ("\n\n[Note: one or more citation marks were removed "
                      "by the server-side verifier (S5).]")
        return {"answer": clean, "meta": meta}, 200, None


class SupabaseRetriever:
    """Calls match_chunks_vec then match_chunks_fts; 404-tolerant."""

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


class WebSearchClient:
    """Placeholder search-API client: Tavily or Serper, key from env.

    Returns rows shaped like bdw_chunks (id/title/content/source_url/
    verified/parent_type) so the rest of the pipeline is untouched.
    """

    TAVILY_URL = "https://api.tavily.com/search"
    SERPER_URL = "https://google.serper.dev/search"

    def __init__(self, provider, api_key, timeout=10,
                 snippet_cap=1200, topk=5):
        self.provider = provider
        self.key = api_key
        self.timeout = timeout
        self.cap = snippet_cap
        self.topk = topk

    def _doc(self, title, url, content):
        return {"id": str(uuid.uuid5(uuid.NAMESPACE_URL, url or title)),
                "title": _clean(title, 200),
                "content": _clean(content, self.cap),
                "source_url": url or "",
                "verified": False,
                "parent_type": "web"}

    def search(self, query, k=None):
        k = k or self.topk
        if self.provider == "serper":
            r = requests.post(
                self.SERPER_URL, timeout=self.timeout,
                headers={"X-API-KEY": self.key,
                         "Content-Type": "application/json"},
                json={"q": query, "num": k})
        else:
            r = requests.post(
                self.TAVILY_URL, timeout=self.timeout,
                json={"api_key": self.key, "query": query,
                      "max_results": k, "search_depth": "basic",
                      "include_answer": False})
        r.raise_for_status()
        body = r.json()
        if self.provider == "serper":
            raw = [(o.get("title"), o.get("link"), o.get("snippet"))
                   for o in body.get("organic", [])]
        else:
            raw = [(x.get("title"), x.get("url"), x.get("content"))
                   for x in body.get("results", [])]
        seen, out = set(), []
        for title, url, content in raw:
            d = self._doc(title, url, content)
            if d["id"] in seen:
                continue
            seen.add(d["id"])
            out.append(d)
        return out[:k]


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

        def _send(self, code, body, ctype="application/json"):
            raw = body if isinstance(body, bytes) else json.dumps(body).encode()
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("Access-Control-Allow-Origin", "*")
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
            web_mode = body.get("web")
            if web_mode is not None and web_mode not in ("auto", "on", "off"):
                return self._send(400, {"error": "web must be auto|on|off"})
            history = body.get("history")
            if history is not None and not isinstance(history, list):
                return self._send(400, {"error": "history must be a list"})
            if not q or len(q) > 600:
                return self._send(400, {"error": "question 1..600 chars"})
            try:
                data, code, err = g.ask(q, uid, web_mode, history)
            except Exception as exc:  # noqa: BLE001
                import traceback; traceback.print_exc()
                data, code, err = {"error": "upstream failure", "detail": str(exc)[:160]}, 502, None
            self._send(code, err or data)

        def do_OPTIONS(self):
            self.send_response(204)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods",
                             "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers",
                             "Content-Type, X-User-Id")
            self.send_header("Access-Control-Max-Age", "86400")
            self.end_headers()

        def do_GET(self):
            path = urllib.parse.urlparse(self.path).path
            if path in ("/", "/index.html"):
                page = os.path.join(os.path.dirname(
                    os.path.abspath(__file__)), "static", "index.html")
                try:
                    with open(page, "rb") as fh:
                        return self._send(200, fh.read(),
                                          ctype="text/html; charset=utf-8")
                except OSError:
                    return self._send(404, {"error": "static page missing"})
            if path == "/health":
                return self._send(200, {"ok": True,
                                        "ts": time.strftime("%H:%M:%S")})
            self._send(404, {"error": "not found"})
    return H


def main():
    import os
    ph3 = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(ph3, ".env")
    if not os.path.isfile(env_path):
        env_path = os.path.join(os.path.dirname(ph3), ".env")
    env = {}
    with open(env_path, encoding="utf-8-sig") as fh:
        for line in fh:
            line = line.strip()
            if line and not line.startswith("#"):
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip()
    for k, v in os.environ.items():
        env[k] = v

    retriever = SupabaseRetriever(env["SUPABASE_URL"],
                                  env["SUPABASE_SERVICE_ROLE_KEY"])
    llm = Zone3LLM(env.get("ZONE3_BASE_URL", "http://127.0.0.1:8080"),
                   int(env.get("ZONE3_TIMEOUT_S", "15")))
    provider = env.get("WEB_SEARCH_PROVIDER", "tavily")
    web_key = env.get("TAVILY_API_KEY" if provider == "tavily"
                      else "SERPER_API_KEY", "")
    web = None
    if web_key:
        web = WebSearchClient(provider, web_key,
                              timeout=int(env.get("WEB_TIMEOUT_S", "10")),
                              snippet_cap=int(
                                  env.get("WEB_SNIPPET_MAX_CHARS", "1200")),
                              topk=int(env.get("WEB_TOPK", "5")))
    cfg = {"RETRIEVAL_TOPK": int(env.get("RETRIEVAL_TOPK", "20")),
           "MAX_TOKENS": int(env.get("MAX_TOKENS", "1024")),
           "RATE_LIMIT_PER_USER_DAY": int(
               env.get("RATE_LIMIT_PER_USER_DAY", "35")),
           "WEB_RAG_MODE": env.get("WEB_RAG_MODE", "auto"),
           "WEB_TOPK": int(env.get("WEB_TOPK", "5"))}
    gate = Gateway(retriever, llm, cfg, web=web)
    port = int(env.get("ZONE2_PORT", "8787"))
    srv = ThreadingHTTPServer(("0.0.0.0", port), handler_class(gate))
    print("RESULT: P3_ZONE2_UP port=%d web=%s provider=%s"
          % (port, "on" if web else "disabled", provider), flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
