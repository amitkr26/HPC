# schema_audit — v0.2, produced 2026-10-27 by agent self-audit

Audit performed by reading the PostgREST OpenAPI spec (service role,
`GET /rest/v1/`, 70 tables) and sampling row counts + representative rows
per candidate table (owner's checklist was reported done but the file was
absent from the workspace; the audit column below was rebuilt from the live
schema rather than the owner's dashboard notes). Owner should re-read this
file and override anything that contradicts what the UI actually serves.

## Data-driven table mapping (+ row counts as of today)

- opportunity -> opportunities (1,090 total; 923 verification_status
  `verified`, 167 `expired`; 511 is_active=true / 579 false) -> we ingest the
  active surface only (what the UI shows users); `verified_values` maps the
  status enum to the truthy flag (sample: `verified`).
- organization -> organizations (288 total; 283 is_active=true); boolean
  `is_verified` used directly.
- resource -> resources (23 rows, is_active all true). `resource_bank`
  (10 rows, no name/title/description columns) rejected: metadata-only
  YouTube channel list, too thin to chunk meaningfully.
- news -> news_articles (1,486 total; 1,279 is_active=true / 207 stale) ->
  active surface only.
- faq: ABSENT from the live schema (no Q&A table); `announcements` exists
  but is EMPTY (0 rows) -> no entry.
- lab_tool: ABSENT from the live schema (no tools table) -> no entry.
- jobs (5 rows) + job_occurrences (job radar): out of scope for RAG v1 —
  tiny/ephemeral scraped rows, candidate for a later expansion pass.

## Schema drift vs the P2.1 column map

Resolved automatically: title/location/eligibility/stipend->salary_range/
deadline/posted->posted_date/url->source_url/description/category on
opportunities; title<-name on organizations+resources; summary->description
on news. NOT resolvable: opportunity `org` (only the FK `organization_id`)
-> handled by `org_via` joining organizations.name in the gateway.

```json
{
  "tables": {
    "opportunity": {"table": "opportunities", "verified": "verification_status",
                    "verified_values": ["verified"], "org_via": "organization_id",
                    "where": {"is_active": "eq.true"}},
    "organization": {"table": "organizations", "verified": "is_verified",
                     "where": {"is_active": "eq.true"}},
    "resource": {"table": "resources", "where": {"is_active": "eq.true"}},
    "news": {"table": "news_articles", "where": {"is_active": "eq.true"}}
  }
}
```

## Notes
- `where` filters keep the corpus equal to the UI's active surface; counts
  above are the pre-filter totals (post-filter totals land in
  ingest_manifest.json).
