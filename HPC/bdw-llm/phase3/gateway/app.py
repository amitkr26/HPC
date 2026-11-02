"""Zone 2 gateway - P3.4 (blueprint): retrieval -> prompt -> Zone 3 -> S5
citation verifier -> respond. Stdlib http.server + requests only; the
retriever, LLM call and web-search client are injected so unit runs can
stub them offline.

Handlers:
  POST /ask   {"question": str, "user_id": str?, "web": "auto"|"on"|"off"?}
              200 {"answer", "citations", "meta"}
  GET  /health

P4 routing (Phase 4 blueprint §4/§5): every question is classified by
phase4/router/domain_classifier.py. The RoutingDecision decides retrieval,
prompt head and Zone 3 LoRA:
  * retrieval  - decision.rag_index ("idx_<domain>") resolves to the dedicated
    Supabase pgvector table public.p4_domain_<domain> through the service-role
    RPC match_p4_<domain>_chunks (P4.4; bge-small-en-v1.5 query embeddings,
    cosine top-k, rows shaped exactly like bdw_chunks so fmt_chunks, the
    citation allowlist and the S5 verifier stay untouched). P4_DOMAIN_BACKEND
    auto|supabase|local selects the path; RPC failure or an empty hit set
    falls back to the local phase4/rag/idx_<domain> npz index. idx_general and
    any index miss/failure fall back to the production Supabase FTS path
    unchanged.
  * prompt     - classifier.prompt_prefix(domain) is prepended by
    build_ask_prompt (the _DOMAIN_PROMPT_PREFIX table in the router).
  * Zone 3     - decision.adapter ("lora_<domain>") is activated per request
    through llama-server's request-scoped "lora" field: run_stack.sh attaches
    the export/p4_lora_<domain>.gguf files with --lora-init-without-apply
    (scale 0) and per request the gateway sends {"lora": [{"id": N,
    "scale": 1.0}]}, resolving N from GET /lora-adapters' paths. General
    questions omit the field, so the base model serves them. If llama-server
    has no adapters attached (P4_ADAPTERS empty at boot) the gateway degrades
    to base-only and logs it once.

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

import sys
_PH4_ROUTER = os.path.join(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))), "phase4", "router")
if _PH4_ROUTER not in sys.path:
    sys.path.insert(0, _PH4_ROUTER)
from domain_classifier import DomainClassifier, RoutingDecision

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

# --- P4 Zone 2 defaults (overridable via env in main()) ---------------------
PH4_DOMAINS = ("math", "vlsi", "embedded", "cs", "aiml")
PH4_RAG_DIR = os.path.join(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))), "phase4", "rag")
PH4_BGE_DIR = os.path.join(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))), "phase3", "models",
    "bge-small-en-v1.5")
PH4_MIN_SIM = 0.30   # cosine cut for domain-index rows (mis-routing guard)
PH4_EMB_THREADS = 2  # torch threads for the query embedder (CPU)
PH4_DOMAIN_TOPK = 8  # focused context: CPU prompt-eval stays inside CTX
PH4_DOMAIN_BACKEND = "auto"  # auto|supabase|local (P4.4 wiring)


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


def build_ask_prompt(context, history, question, web_used=False,
                     domain_prefix=None):
    """Gateway-side single source of truth for the /ask prompt: an optional
    domain-specific system prefix, then context (+ web preamble), then the
    threaded conversation, then the question. History entries are filtered
    to role in user|assistant, capped to the last HISTORY_TURNS turns and
    HISTORY_CHAR_CAP chars per turn."""
    prompt = SYSTEM_TEMPLATE.format(context=context)
    if domain_prefix:
        prompt = domain_prefix + "\n" + prompt
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
    def __init__(self, retriever, llm, cfg, web=None,
                 classifier=None, lora_resolver=None):
        self.retriever = retriever
        self.llm = llm
        self.web = web
        self.classifier = classifier or DomainClassifier()
        self.lora_resolver = lora_resolver or (lambda adapter: None)
        self.lim = RateLimiter(cfg["RATE_LIMIT_PER_USER_DAY"])
        self.cfg = cfg

    def ask(self, question, user_id, web_mode=None, history=None):
        if not self.lim.hit(user_id):
            return None, 429, {"error": "rate limit reached; retry tomorrow"}
        mode = web_mode or self.cfg.get("WEB_RAG_MODE", "auto")
        decision = self.classifier.classify(question)  # P4: routing FIRST
        print("P4_DOMAIN domain=%s conf=%.2f adapter=%s index=%s "
              "reason=%s" % (decision.domain, decision.confidence,
                             decision.adapter, decision.rag_index,
                             decision.reason), flush=True)
        try:
            ranked = self.retriever.search(
                question, self.cfg["RETRIEVAL_TOPK"],
                domain=decision.domain.value,
                rag_index=decision.rag_index)
        except TypeError:  # stub/unit retrievers without domain support
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
        domain_prefix = self.classifier.prompt_prefix(decision.domain)
        prompt, n_turns = build_ask_prompt(context, history, question,
                                           web_used, domain_prefix)
        lora_id = self.lora_resolver(decision.adapter)
        if decision.adapter and lora_id is None:
            print("P4_ADAPTER domain=%s adapter=%s state=unavailable "
                  "(serving on base model)" % (
                      decision.domain.value, decision.adapter), flush=True)
        answer = self.llm.complete(
            prompt, max_tokens=self.cfg["MAX_TOKENS"], lora_id=lora_id)
        clean, kept, stale = verify_citations(
            answer, len(ranked), ids)
        meta = {"routing": {"mode": mode, "web_used": web_used,
                            "reason": reason, "history_turns": n_turns},
                "domain": decision.to_dict(),
                "retrieval": {"domain_backend": next(
                    (r.get("backend") for r in ranked
                     if r.get("backend")), None)},
                "lora": {"adapter": decision.adapter,
                         "llama_id": lora_id,
                         "applied": lora_id is not None},
                "citations_kept": kept, "citations_dropped": stale,
                "chunks": [{"id": c, "title": ranked[i].get("title"),
                            "url": ranked[i].get("source_url"),
                            "verified": ranked[i].get("verified"),
                            "source": ranked[i].get("parent_type"),
                            "backend": ranked[i].get("backend")}
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

    def search(self, query, k, domain=None, rag_index=None):
        # domain/rag_index are P4 hooks: production general retrieval stays
        # on bdw_chunks; domain hit handling lives in DomainHybridRetriever.
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


class DomainHybridRetriever:
    """P4 Zone 2 retrieval (blueprint §4/§6.3): route per question to the
    domain's dedicated Supabase pgvector table, recovered from
    RoutingDecision.rag_index.

    * domain != general -> embed the query with the staged P3.1
      bge-small-en-v1.5 on CPU, then (backend auto|supabase) call the
      service-role RPC match_p4_<domain>_chunks(query_embedding,
      match_count, min_similarity). Rows are shaped like bdw_chunks
      (parent_type="domain") and cut at PH4_MIN_SIM so a mis-routed
      question does not drag junk into context.
    * fallback (backend local, RPC error/404, or empty hit set) -> the
      local phase4/rag/idx_<domain> npz index, cosine top-k, same shape.
      This keeps the stack fully offline on the cluster.
    * general domain, missing index, embedder failure or an empty hit set ->
      unchanged production path (Supabase bdw_chunks FTS).
    """

    def __init__(self, base, rag_root=PH4_RAG_DIR, bge_dir=PH4_BGE_DIR,
                 domains=PH4_DOMAINS, min_sim=PH4_MIN_SIM,
                 emb_threads=PH4_EMB_THREADS, domain_topk=PH4_DOMAIN_TOPK,
                 backend=PH4_DOMAIN_BACKEND):
        self.base = base
        self.rag_root = rag_root
        self.bge_dir = bge_dir
        self.domains = tuple(domains)
        self.min_sim = float(min_sim)
        self.emb_threads = emb_threads
        self.domain_topk = int(domain_topk)
        self.backend = str(backend or "auto").lower()
        self._lock = threading.Lock()
        self._indexes = {}   # domain -> (vectors np, chunks list)
        self._model = None   # lazy SentenceTransformer
        self._emb_failed = set()  # domain names whose load failed once
        self._sb_down = False     # Supabase domain RPC failed once
        self.stats = {}      # domain -> ("supabase"|"domain"|"fallback", n)

    # -- internals ---------------------------------------------------------

    def _index_server(self, domain):
        if domain in self._indexes:
            return self._indexes[domain]
        if domain in self._emb_failed or domain not in self.domains:
            return None
        vec_path = os.path.join(self.rag_root, "idx_" + domain,
                                "vectors.npy")
        meta_path = os.path.join(self.rag_root, "idx_" + domain,
                                 "meta.json")
        try:
            import numpy as np
            vecs = np.load(vec_path)
            with open(meta_path, encoding="utf-8") as fh:
                chunks = json.load(fh)["chunks"]
            assert vecs.ndim == 2 and vecs.shape[1] == 384, \
                "unexpected vector shape %r" % (vecs.shape,)
            assert len(chunks) == vecs.shape[0], \
                "meta/vectors drift: %d vs %d" % (len(chunks), vecs.shape[0])
        except Exception:  # noqa: BLE001
            import traceback
            traceback.print_exc()
            self._emb_failed.add(domain)
            return None
        self._indexes[domain] = (vecs, chunks)
        return self._indexes[domain]

    def _embedder(self):
        with self._lock:
            if self._model is not None:
                return self._model
            try:
                import torch
                from sentence_transformers import SentenceTransformer
                torch.set_num_threads(int(self.emb_threads))
                self._model = SentenceTransformer(self.bge_dir,
                                                  device="cpu")
            except Exception:  # noqa: BLE001
                import traceback
                traceback.print_exc()
                return None
            return self._model

    def _shape(self, chunk, score):
        text = (chunk.get("text") or chunk.get("content") or "").strip()
        return {"id": chunk.get("id"),
                "title": chunk.get("title") or "",
                "content": text,
                "source_url": chunk.get("url")
                or chunk.get("source_url") or "",
                "verified": True,
                "parent_type": "domain",
                "domain": chunk.get("domain"),
                "score": round(float(score), 4),
                "backend": "local"}

    def _supabase_rows(self, domain, q, k):
        """P4.4: vector search through match_p4_<domain>_chunks (service
        role). Similarity cut is applied server-side by the RPC, matching
        the local path's top-k-then-threshold behavior."""
        payload = {"query_embedding": [round(float(x), 6) for x in q],
                   "match_count": int(self.domain_topk),
                   "min_similarity": float(self.min_sim)}
        rows = self.base.rpc("match_p4_%s_chunks" % domain, payload)
        out = []
        for r in rows or []:
            out.append({"id": r.get("id"),
                        "title": r.get("title") or "",
                        "content": (r.get("content") or "").strip(),
                        "source_url": r.get("source_url") or "",
                        "verified": True,
                        "parent_type": "domain",
                        "domain": domain,
                        "score": round(float(r.get("similarity") or 0.0), 4),
                        "backend": "supabase"})
        out.sort(key=lambda r: -r["score"])
        return out[:k]

    # -- public API --------------------------------------------------------

    def search(self, query, k, domain=None, rag_index=None):
        if domain and domain != "general" and domain in self.domains:
            q = None
            model = self._embedder()
            if model is not None:
                try:
                    q = model.encode([query],
                                     normalize_embeddings=True)[0]
                except Exception:  # noqa: BLE001
                    import traceback
                    traceback.print_exc()
            # 1) dedicated Supabase domain table (production path, §6.3)
            if (q is not None and self.backend in ("auto", "supabase")
                    and not self._sb_down
                    and hasattr(self.base, "rpc")):
                try:
                    rows = self._supabase_rows(domain, q, k)
                    if rows:
                        self.stats[domain] = ("supabase", len(rows))
                        return rows
                    self.stats[domain] = ("supabase", 0)
                except Exception as e:  # noqa: BLE001
                    print("P4_DOMAIN_BACKEND state=supabase_failed "
                          "domain=%s error=%s fallback=local"
                          % (domain, str(e)[:140]), flush=True)
                    self._sb_down = True
            # 2) local npz index (offline cluster / RPC outage fallback)
            try:
                idx = self._index_server(domain)
                if idx is not None and q is not None:
                    vecs, chunks = idx
                    import numpy as np
                    scores = vecs @ np.asarray(q, dtype=vecs.dtype)
                    k_eff = min(int(self.domain_topk), len(chunks))
                    top = np.argpartition(-scores, k_eff - 1)[:k_eff]
                    top = top[np.argsort(-scores[top])]
                    rows = [self._shape(chunks[i], scores[i])
                            for i in top]
                    rows = [r for r in rows
                            if r["score"] >= self.min_sim][:k]
                    if rows:
                        self.stats[domain] = ("local", len(rows))
                        return rows
                    self.stats[domain] = ("fallback", 0)
            except Exception:  # noqa: BLE001
                import traceback
                traceback.print_exc()
        return self.base.search(query, k)


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
    """llama-server client. Two activation modes for P4 LoRA adapters:
    * llama-server started WITH attached adapters (--lora + optional
      --lora-init-without-apply): per-request selection through the
      request-scoped "lora" field: {"lora": [{"id": N, "scale": 1.0}]}.
      lora_ids maps "lora_<domain>" -> N via GET /lora-adapters paths.
    * llama-server started WITHOUT adapters (legacy P3 stack): requests
      carry no lora field; complete() must not add it.
    """

    def __init__(self, base, timeout):
        self.base = base.rstrip("/")
        self.timeout = timeout
        self.lora_ids = None       # {"lora_math": 0, ...} | None (no attach)
        self._lora_failed = False  # probe error cached -> base-only serving

    def refresh_lora_map(self, tries=6, delay=2):
        """GET /lora-adapters; build name->id map from export paths.
        Returns the map or None when the server has no P4 adapters (or is
        unreachable). Brief retry loop covers the gateway booting before
        the llama-server model finishes loading. Result cached; call once
        at boot (llama ids do not change after startup)."""
        if self._lora_failed:
            return self.lora_ids
        for attempt in range(tries):
            try:
                r = requests.get(self.base + "/lora-adapters",
                                 timeout=min(self.timeout, 10))
                r.raise_for_status()
                ids = {}
                for item in r.json():
                    m = re.search(r"p4_lora_(%s)\.gguf$" %
                                  "|".join(PH4_DOMAINS),
                                  os.path.basename(item.get("path") or ""))
                    if m:
                        ids["lora_" + m.group(1)] = int(item["id"])
                self.lora_ids = ids or None
                return self.lora_ids
            except Exception:  # noqa: BLE001
                if attempt < tries - 1:
                    time.sleep(delay)
        self._lora_failed = True
        self.lora_ids = None
        return None

    def complete(self, prompt, max_tokens=1024, lora_id=None):
        """Serves through /v1/chat/completions so llama-server renders the
        merged GGUF's chat template server-side (the P2/P4 SFT rows were
        chat-templated messages; raw /completion prompts underfit the
        adapters). The whole gateway prompt (domain prefix + instructions +
        numbered context + question) ships as a single user message, the
        exact shape the P3 prompt contract defined. Optional request-scoped
        LoRA: {"lora": [{"id": N, "scale": 1.0}]} (llama ids from
        refresh_lora_map)."""
        body = {"messages": [{"role": "user", "content": prompt}],
                "max_tokens": int(max_tokens), "temperature": 0.0,
                "stream": False}
        if lora_id is not None:
            body["lora"] = [{"id": int(lora_id), "scale": 1.0}]
        r = requests.post(self.base + "/v1/chat/completions",
                          timeout=self.timeout, json=body)
        r.raise_for_status()
        data = r.json()
        try:
            return data["choices"][0]["message"].get("content") or ""
        except (KeyError, IndexError, TypeError):
            raise RuntimeError("no chat content in llama answer: %s"
                               % str(data)[:160])


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


class _NoBaseStub:
    """Base-retriever stand-in for the offline self-test (must never be
    hit when the domain indexes answer)."""

    def search(self, query, k, domain=None, rag_index=None):
        return []


def ph4_selftest():
    """Offline Zone 2 routing verification (no Zone 3, no Supabase):
    (1) the router names the expected domain/adapter/index for the six
    canonical cases; (2) build_ask_prompt really prepends the domain
    _DOMAIN_PROMPT_PREFIX; (3) every domain case retrieves from its local
    npz index with bge on CPU (top row >= PH4_MIN_SIM, parent_type domain;
    the _NoBaseStub fallback must stay untouched)."""
    clf = DomainClassifier()
    ret = DomainHybridRetriever(_NoBaseStub())
    cases = [
        ("explain setup and hold time in cmos", "vlsi", "idx_vlsi"),
        ("stm32 gpio interrupt handler in bare metal c",
         "embedded", "idx_embedded"),
        ("derive the gradient of a convex loss function", "math", "idx_math"),
        ("big-o complexity of graph traversal", "cs", "idx_cs"),
        ("fine-tune a transformer with lora on a single gpu",
         "aiml", "idx_aiml"),
        ("hello how are you", "general", "idx_general"),
    ]
    ok = True
    for q, want_dom, want_idx in cases:
        dec = clf.classify(q)
        prefix = clf.prompt_prefix(dec.domain)
        prompt, _ = build_ask_prompt("[]", [], q, False, prefix)
        domain_set = prompt.startswith(prefix + "\nYou are the BDW "
                                                "assistant.")
        info = {"q": q, "domain": dec.domain.value,
                "adapter": dec.adapter, "rag_index": dec.rag_index,
                "prefix_ok": domain_set}
        if dec.domain.value == "general":
            info["retrieved"] = 0
            hits_ok = dec.rag_index == "idx_general"
        else:
            rows = ret.search(q, 20, domain=dec.domain.value,
                              rag_index=dec.rag_index)
            info["retrieved"] = len(rows)
            info["top_score"] = rows[0]["score"] if rows else None
            hits_ok = (rows and rows[0]["parent_type"] == "domain"
                       and rows[0]["score"] >= PH4_MIN_SIM)
        match = (dec.domain.value == want_dom
                 and dec.rag_index == want_idx
                 and dec.adapter == (None if want_dom == "general"
                                     else "lora_" + want_dom)
                 and domain_set and hits_ok)
        ok = ok and match
        print(json.dumps(info, ensure_ascii=False))
        print("EXPECT domain=%s index=%s -> %s"
              % (want_dom, want_idx, "PASS" if match else "FAIL"))
    print("RESULT: %s" % ("P4_ZONE2_SELFTEST_OK" if ok
                          else "P4_ZONE2_SELFTEST_FAIL"))
    return 0 if ok else 1


def load_env():
    """phase3/gateway/.env (or phase3/.env), then os.environ overrides."""
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
    return env


def supabase_selftest():
    """Live P4.4 verification: all 5 domain tables readable and all 5 RPCs
    callable through the service role. Uses a fixed unit vector (any vector
    is valid for cosine distance) so no embedder load is needed."""
    env = load_env()
    sb = SupabaseRetriever(env["SUPABASE_URL"],
                           env["SUPABASE_SERVICE_ROLE_KEY"])
    vec = "[" + ",".join(["1.0"] + ["0.0"] * 383) + "]"
    ok = True
    for d in PH4_DOMAINS:
        tbl = "p4_domain_" + d
        try:
            r = requests.get("%s/rest/v1/%s?select=id&limit=1"
                             % (sb.url, tbl),
                             headers={"apikey": sb.svc,
                                      "Authorization": "Bearer " + sb.svc},
                             timeout=20)
            table_ok = r.status_code == 200
            rows = sb.rpc("match_p4_%s_chunks" % d,
                          {"query_embedding": vec, "match_count": 2,
                           "min_similarity": 0.0})
            rpc_ok = isinstance(rows, list) and len(rows) >= 1
            print("RESULT: P4_SUPABASE_%s_%s table=%s rpc_rows=%d"
                  % (d.upper(), "OK" if (table_ok and rpc_ok) else "FAIL",
                     "readable" if table_ok else "http_%d" % r.status_code,
                     len(rows or [])))
            ok = ok and table_ok and rpc_ok
        except Exception as e:  # noqa: BLE001
            print("RESULT: P4_SUPABASE_%s_FAIL %s" % (d.upper(), e))
            ok = False
    print("RESULT: %s" % ("P4_ZONE2_SUPABASE_OK domains=5" if ok
                          else "P4_ZONE2_SUPABASE_FAIL"))
    return 0 if ok else 1


def main():
    import argparse
    ap = argparse.ArgumentParser(description="Zone 2 gateway (P3.4 + P4)")
    ap.add_argument("--self-test", action="store_true",
                    help="offline P4 routing/retrieval verification; "
                         "no server boot")
    ap.add_argument("--supabase-selftest", action="store_true",
                    help="live P4.4 check: domain tables + RPCs reachable")
    args, _ = ap.parse_known_args()
    if args.self_test:
        return ph4_selftest()
    if args.supabase_selftest:
        return supabase_selftest()

    env = load_env()

    base_retriever = SupabaseRetriever(env["SUPABASE_URL"],
                                       env["SUPABASE_SERVICE_ROLE_KEY"])
    rag_root = env.get("PH4_RAG_DIR", PH4_RAG_DIR)
    bge_dir = env.get("PH4_BGE_DIR", PH4_BGE_DIR)
    domain_backend = env.get("P4_DOMAIN_BACKEND",
                             PH4_DOMAIN_BACKEND).lower()
    retriever = DomainHybridRetriever(
        base_retriever, rag_root=rag_root, bge_dir=bge_dir,
        min_sim=float(env.get("PH4_MIN_SIM", PH4_MIN_SIM)),
        emb_threads=int(env.get("PH4_EMB_THREADS", PH4_EMB_THREADS)),
        domain_topk=int(env.get("PH4_DOMAIN_TOPK", PH4_DOMAIN_TOPK)),
        backend=domain_backend)

    # P4.4: read-only probe of the dedicated Supabase domain tables so the
    # boot record states which retrieval path will serve domain questions.
    sb_tables = "skipped"
    if domain_backend in ("auto", "supabase"):
        try:
            r = requests.get(
                "%s/rest/v1/p4_domain_math?select=id&limit=1"
                % base_retriever.url,
                headers={"apikey": base_retriever.svc,
                         "Authorization": "Bearer " + base_retriever.svc},
                timeout=20)
            sb_tables = "ok" if r.status_code == 200 else \
                "missing(http_%d)" % r.status_code
        except Exception:  # noqa: BLE001
            sb_tables = "unreachable"
        print("RESULT: P4_SUPABASE_DOMAINS state=%s backend=%s tables=%s"
              % (sb_tables, domain_backend,
                 "p4_domain_math,vlsi,embedded,cs,aiml"), flush=True)
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

    # P4: discover which adapters llama-server actually attached (paths
    # from GET /lora-adapters) so per-request ids match the runtime truth.
    llama_ids = llm.refresh_lora_map()
    llama_attached = sorted(llama_ids.keys()) if llama_ids else []

    def lora_resolver(adapter):
        if not adapter:
            return None
        ids = llama_ids or {}
        return ids.get(adapter)

    gate = Gateway(retriever, llm, cfg, web=web,
                   lora_resolver=lora_resolver)
    port = int(env.get("ZONE2_PORT", "8787"))
    srv = ThreadingHTTPServer(("0.0.0.0", port), handler_class(gate))
    home = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))
    present = [d for d in PH4_DOMAINS
               if os.path.isfile(os.path.join(rag_root, "idx_" + d,
                                              "vectors.npy"))]
    print("RESULT: P3_ZONE2_UP port=%d web=%s provider=%s"
          % (port, "on" if web else "disabled", provider), flush=True)
    print("RESULT: P4_ZONE2_UP port=%d retriever=domain_hybrid "
          "domain_backend=%s supabase_tables=%s rag_dir=%s "
          "indexes_present=%s min_sim=%.2f domain_topk=%d "
          "llama_attached=%s" % (
              port, retriever.backend, sb_tables,
              os.path.relpath(rag_root, home) if home else rag_root,
              ",".join(present), retriever.min_sim, retriever.domain_topk,
              ",".join(llama_attached) or "none"), flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    rc = main()
    if rc is not None:
        sys.exit(rc)
