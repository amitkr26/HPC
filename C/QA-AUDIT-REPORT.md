# Live QA Audit Report — BerojgarDegreeWala

**Target:** https://berojgardegreewala.vercel.app
**Audit date:** 11 August 2026
**Method:** Playwright (Chromium) browser automation + direct HTTP probing (curl/Node.js) against the production deployment
**Build ID inspected:** `6U9dx4idtqlzC3bu4lphI`

---

## 1. Executive Summary

The platform is **functionally deployed and broadly working** — opportunities, news, organizations, academy, chat, resources, and signup pages all render, the admin console is properly gated, and security headers are strong. However, the audit found **3 high-severity broken features** (search, contact form, and social/OG image sharing), **2 medium issues** (news title corruption, missing unsubscribe path), and several data-integrity / SEO gaps. Notably, the **AI assistant — a headline feature — is not connected to the platform's own database**.

### Key stats verified against the live API
| Claim | Actual (API) | Verdict |
|---|---|---|
| 3269+ active opportunities | `total_count = 3269` | ✅ Accurate |
| 88+ organizations tracked | 88 returned | ✅ Accurate |
| 33+ news articles (About page) | 2500+ articles | ❌ Stale/undercount |
| 3167+ JRF fellowships | 3216 (category=jrf) | ✅ Accurate |
| 38+ PhD programs | 61 (category=phd) | ✅ Accurate (undersells) |

---

## 2. Findings by Severity

### 🔴 P1 — Critical / User-facing broken features

#### P1-1. Sitewide search is completely broken (`/api/search` → 404)
- The `/search` page calls `GET /api/search?q=DRDO&page=1`, which returns **HTTP 404**.
- Result: every search shows **"0 results"**, even for "DRDO" — which returns **67 records** via the working `/api/opportunities?search=DRDO`.
- Users cannot find anything through the search feature.
- **Evidence:**
  - `api/search?q=DRDO => HTTP:404`
  - Search page body text: `0 results`
  - `api/opportunities?search=DRDO => HTTP:200` (67 results)

#### P1-2. Contact / feedback form silently fails (`/api/contact` → 404)
- Submitting the contact form POSTs to `/api/contact`, which returns **HTTP 404**.
- The page still displays **"Thank You!"** after submit, so users believe their message was sent when it never reached anyone.
- **Evidence:** Playwright form submission → `REQ POST /api/contact` → `RESP 404` → UI shows `Thank You!`.

#### P1-3. OpenGraph image is empty — social sharing broken sitewide (`/api/og` → 0 bytes)
- Every page declares `og:image` / `twitter:image` = `https://berojgardegreewala.vercel.app/api/og`.
- `GET /api/og` returns **HTTP 200 with `Content-Type: image/png` but 0 bytes**.
- WhatsApp, LinkedIn, X/Twitter cards will render with a broken/missing image for the entire site.
- **Evidence:** `OG: 200 ct:image/png sz:0`; downloaded file size = 0 bytes.

#### P1-4. AI Career Assistant is not connected to the platform's own database
- Asked *"What are the latest JRF opportunities in VLSI design in India?"*, the assistant replied:
  > *"I'm not aware of the current JRF opportunities in VLSI design in India."*
- This contradicts the platform's core value prop ("100% verified research openings") — the site has **3,269 opportunities, 3,216 JRF/SRF fellowships, 67 DRDO openings**.
- The assistant also **hallucinated a URL**: it recommended `www.iit.ac.in` (not a real IIT domain).
- Impact: the marquee "AI Career Tools" feature actively misleads users and fails at its primary job.

---

### 🟠 P2 — Medium

#### P2-1. News detail pages show corrupted titles
- Detail page for `india-semiconductor-mission-approves-15b-chip-fab-projects-july-2026` displays:
  > "India Semiconductor Mission Approves **15b** Chip Fab Projects **July 2026**"
- The actual stored title (from `/api/news?search=India+Semiconductor`) is:
  > "India Semiconductor Mission Approves **$15B** Chip Fab Projects **in Gujarat and Assam**"
- Root cause: the detail page renders a **slug-derived title** (de-slugified, `$`/comma-stripped, "B" lowercased, trailing words dropped) instead of the stored title. Affects all news articles whose titles contain `$`, numbers, or more words than the slug.

#### P2-2. Newsletter subscribers cannot unsubscribe (`/api/unsubscribe` → 404)
- `POST /api/unsubscribe` returns **404** (the endpoint does not exist).
- There is no other unsubscribe mechanism on the site.
- Under India's DPDP Act 2023 (which the site itself cites on the Contact page), a data subject must be able to withdraw consent. This is a compliance gap.
- ⚠️ **Note to owner:** a test subscription `qa-audit-test@example.com` was created during this audit; it cannot be removed via the public API. Please purge it manually from Supabase.

#### P2-3. News single-article API is broken (`/api/news/[slug]` → 404)
- `GET /api/news/waymo-extends-driverless-lead` → `404 {"error":"Article not found"}`.
- News detail *pages* render (server-side), but the underlying public API for a single article 404s — inconsistent and blocks any client-side deep-linking/integration.

#### P2-4. `/search` page category vocabulary is inconsistent
- The `/search` page dropdown offers: `Govt Job`, `Private Job`, `Fellowship`.
- The `/opportunities` filters and footer use different slugs: `government`, `job`, `internship`, `jrf`, `srf`, `phd`.
- `category=phy` (not a real category) silently returns 137 results rather than rejecting it — lenient/ambiguous category handling.

---

### 🟡 P3 — Low / Hygiene / SEO / Content

#### P3-1. Pagination is ignored by the organizations API
- `GET /api/organizations?per_page=10&page=1` and `...&page=2` return **the same 88 organizations** in the same order.
- `per_page` is also ignored. Opportunity/news APIs paginate correctly; orgs does not.

#### P3-2. Sitemap is incomplete
- Sitemap.xml contains **1053 URLs**: 1000 opportunities, 5 resources, ~48 static pages, and **0 news article URLs** (out of 2500+).
- Only 1000 of 3269 opportunity pages are in the sitemap.

#### P3-3. Stale statistics
- About page: "**33+ News Articles**" — actual count is **2500+**.
- The news aggregation engine ("Auto-synced with live IEEE Spectrum, EE Times & SemiEngineering feeds") surfaces articles from **Electronics Weekly** (and likely other feeds) without the label matching the described sources.

#### P3-4. No `/robots.txt` news coverage & admin page is indexable
- `robots.txt` correctly disallows `/admin` and `/api/`, and references a valid sitemap.
- The `/admin` login page itself serves `<meta name="robots" content="index, follow">` — an admin portal is being indexed by search engines (minor info-exposure / phishing surface).

#### P3-5. `www.iit.ac.in` hallucination (see P1-4) — also a content-hygiene item
- Recommending a parked/incorrect domain as an official IIT portal is dangerous (typosquatting risk for students).

---

## 3. Security Assessment

### ✅ Strengths (verified passing)
| Check | Result |
|---|---|
| **CSP header** | Present with restrictive `default-src 'self'`, explicit `script-src` allowlist, `object-src 'none'`, `base-uri 'self'`, `form-action 'self'`, CSP report URI |
| **HSTS** | `max-age=31536000; includeSubDomains; preload` |
| **X-Frame-Options** | `DENY` (clickjacking protection) |
| **X-Content-Type-Options** | `nosniff` |
| **Referrer-Policy** | `strict-origin-when-cross-origin` |
| **Permissions-Policy** | `camera=(), microphone=(), geolocation=()` |
| **Admin auth** | `/api/admin/auth` returns 401 for invalid creds; 14 common default passwords all rejected |
| **Admin console** | `/admin` requires username + password; no bypass found |
| **Secret exposure** | No `.env`, `.git`, `vercel.json`, `next.config.js`, `package.json` exposed (all 404). Only public Supabase **anon** key + Supabase URL in JS bundles (normal for Supabase) |
| **Service-role key** | Not present in client bundles — only referenced as server-side env |
| **Open redirects** | `?next=`, `?redirect=` to external domains → no redirect |
| **CSP-report endpoint** | `POST /api/csp-report` → 204 (works) |
| **OG image** | 🔴 Broken (P1-3) |

### ⚠️ Residual observations
- `script-src` includes `'unsafe-eval'` and `'unsafe-inline'` — common for Next.js but weakens CSP value somewhat.
- No obvious rate limiting observed on public read APIs during the audit (only one transient empty-response from `/api/opportunities`).
- No brute-force lockout observed on `/api/admin/auth` (did not exhaustively test to avoid noise).

---

## 4. Test Coverage Summary

| Area | Method | Pages / Endpoints | Status |
|---|---|---|---|
| Core pages | Playwright navigation + text extraction | `/`, `/opportunities`, `/news`, `/about`, `/contact`, `/search`, `/organizations`, `/academy`, `/chat`, `/ask-ai`, `/resume`, `/network`, `/signup`, `/admin`, `/resources/*`, news detail, opportunity detail | ✅ Rendered |
| Read APIs | Direct HTTP | `/api/opportunities`, `/api/organizations`, `/api/news`, `/api/news/[slug]`, `/api/search`, `/api/og`, `/api/csp-report`, `/api/contact`, `/api/subscribe`, `/api/unsubscribe`, `/api/auth/check-username` | ⚠️ 5 broken (see §2) |
| Write APIs (non-destructive only) | Playwright + curl | Newsletter subscribe (created test record), contact submit (failed by design) | ⚠️ See P2-2 note |
| Security | Header capture, payload scanning, credential probing, path fuzzing | See §3 | ✅ Good |
| SEO | `robots.txt`, `sitemap.xml` parse | 1053 URLs, 0 news | ⚠️ P3-2 |

**Deliberately not tested (per audit scope):** destructive admin actions, brute-forcing admin beyond common defaults, creating user accounts, or posting content to the database.

---

## 5. Recommended Fix Priorities

1. **P1-1 Search:** implement `/api/search` (or point the page at `/api/opportunities?search=...`) — the search page UI and the working opportunities search already exist; this is a missing route.
2. **P1-2 Contact:** add `/api/contact` handler or wire the form to an existing email/DB endpoint; stop showing "Thank You!" on failure.
3. **P1-3 OG image:** fix `/api/og` to return a real PNG (1200×630); verify with `curl -o og.png` that bytes > 0.
4. **P1-4 AI grounding:** connect the chat assistant to the opportunities/news database (RAG/retrieval over the 3269 records), add a "disclaimer + source links" response mode, and guard against hallucinated URLs.
5. **P2-1 News titles:** render `title` from the stored record, not from the slug.
6. **P2-2 Unsubscribe:** implement `DELETE /api/subscribe/:email` (or a token-based unsubscribe link in digest emails).
7. **P3:** fix orgs pagination, regenerate sitemap to include news + all opportunities, update the "33+ News Articles" stat, add `noindex` to `/admin`.
8. **Purge test data:** delete the `qa-audit-test@example.com` newsletter subscription created during this audit.

---

*Prepared as part of a black-box QA audit of the production deployment. All tests were non-destructive except one newsletter test subscription (flagged in P2-2).*
