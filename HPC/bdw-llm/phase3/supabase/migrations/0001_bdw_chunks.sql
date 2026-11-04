-- Phase 3 milestone P3.0 — bdw_chunks retrieval index (PHASE3_INTEGRATION_BLUEPRINT.md §2)
-- Applied by the owner via Supabase SQL editor or psql; idempotent.
-- Embeddings: bge-small-en-v1.5, 384 dims (§7.2 of BDW_INTEGRATION.md).
-- Hard rule (§7.2): a chunk with no verifiable parent ID is never indexed —
-- enforced by the NOT NULLs here and re-checked by gateway/ingest.py.

create extension if not exists vector;

create table if not exists public.bdw_chunks (
  id            uuid primary key default gen_random_uuid(),
  parent_type   text        not null check (parent_type in
                  ('opportunity','organization','resource','faq','news','lab_tool')),
  parent_id     uuid        not null,
  source_url    text        not null,
  title         text        not null,
  content       text        not null,
  verified      boolean     not null default false,
  embedding     vector(384) not null,
  content_tsv   tsvector    generated always as (to_tsvector('english', content)) stored,
  updated_at    timestamptz not null default now()
);

create index if not exists bdw_chunks_vec_idx
  on public.bdw_chunks using ivfflat (embedding vector_cosine_ops) with (lists = 100);
create index if not exists bdw_chunks_fts_idx
  on public.bdw_chunks using gin (content_tsv);
create index if not exists bdw_chunks_parent_idx
  on public.bdw_chunks (parent_type, parent_id);
create index if not exists bdw_chunks_updated_idx
  on public.bdw_chunks (updated_at);   -- incremental refresh cursor (§7.2)

-- RLS: Zone 4 is read-only for anon; writes and deletes are service-role only.
alter table public.bdw_chunks enable row level security;
drop policy if exists bdw_chunks_anon_read on public.bdw_chunks;
create policy bdw_chunks_anon_read on public.bdw_chunks
  for select to anon, authenticated using (true);
