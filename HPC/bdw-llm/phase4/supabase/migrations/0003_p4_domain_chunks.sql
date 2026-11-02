-- Phase 4 P4.4 - per-domain pgvector retrieval tables (PHASE4_DOMAIN_LORA_BLUEPRINT.md 6.3)
-- Mirrors phase4/rag/idx_<domain>/ exactly: bge-small-en-v1.5, 384 dims,
-- L2-normalised rows, cosine metric (same embedder as production bdw_chunks).
-- Applied by the owner via the Supabase Management API (database/query) or the
-- SQL editor; fully idempotent. ASCII-only (the BDW migration runner strips
-- non-ASCII before sending).
--
-- Security model (S10/S11): these are INTERNAL gateway tables. RLS is enabled
-- with NO anon/authenticated policies and table privileges are revoked from
-- both roles; only service_role (the Zone 2 gateway) can read or write.
-- Retrieval RPCs are SECURITY DEFINER with search_path pinned, execute granted
-- to service_role only -- mirroring phase3/supabase/migrations/0002_match_chunks.sql.
--
-- Row identity: id is the 16-hex chunk id produced by p4_build_rag_index.py
-- (text, not uuid) so local indexes and Supabase stay reconcilable 1:1.
-- source_url is preserved on every row (provenance gate).

create extension if not exists vector;

-- ---------------------------------------------------------------------------
-- 1. Five domain tables (one per Phase 4 router surface; general stays on
--    public.bdw_chunks, which is the production platform corpus).
-- ---------------------------------------------------------------------------
create table if not exists public.p4_domain_math (
  id          text primary key,
  domain      text not null default 'math' check (domain = 'math'),
  title       text not null,
  source_url  text not null,
  content     text not null,
  embedding   extensions.vector(384) not null,
  content_tsv tsvector generated always as (to_tsvector('english', content)) stored,
  verified    boolean not null default true,
  updated_at  timestamptz not null default now()
);

create table if not exists public.p4_domain_vlsi (
  id          text primary key,
  domain      text not null default 'vlsi' check (domain = 'vlsi'),
  title       text not null,
  source_url  text not null,
  content     text not null,
  embedding   extensions.vector(384) not null,
  content_tsv tsvector generated always as (to_tsvector('english', content)) stored,
  verified    boolean not null default true,
  updated_at  timestamptz not null default now()
);

create table if not exists public.p4_domain_embedded (
  id          text primary key,
  domain      text not null default 'embedded' check (domain = 'embedded'),
  title       text not null,
  source_url  text not null,
  content     text not null,
  embedding   extensions.vector(384) not null,
  content_tsv tsvector generated always as (to_tsvector('english', content)) stored,
  verified    boolean not null default true,
  updated_at  timestamptz not null default now()
);

create table if not exists public.p4_domain_cs (
  id          text primary key,
  domain      text not null default 'cs' check (domain = 'cs'),
  title       text not null,
  source_url  text not null,
  content     text not null,
  embedding   extensions.vector(384) not null,
  content_tsv tsvector generated always as (to_tsvector('english', content)) stored,
  verified    boolean not null default true,
  updated_at  timestamptz not null default now()
);

create table if not exists public.p4_domain_aiml (
  id          text primary key,
  domain      text not null default 'aiml' check (domain = 'aiml'),
  title       text not null,
  source_url  text not null,
  content     text not null,
  embedding   extensions.vector(384) not null,
  content_tsv tsvector generated always as (to_tsvector('english', content)) stored,
  verified    boolean not null default true,
  updated_at  timestamptz not null default now()
);

-- HNSW cosine indexes: no training step, good recall at these table sizes
-- (353-736 rows/domain). The RPC orders by <=> in a subquery so the index is
-- usable; the similarity cut is applied after the top-k window.
create index if not exists p4_domain_math_vec_idx
  on public.p4_domain_math using hnsw (embedding extensions.vector_cosine_ops);
create index if not exists p4_domain_vlsi_vec_idx
  on public.p4_domain_vlsi using hnsw (embedding extensions.vector_cosine_ops);
create index if not exists p4_domain_embedded_vec_idx
  on public.p4_domain_embedded using hnsw (embedding extensions.vector_cosine_ops);
create index if not exists p4_domain_cs_vec_idx
  on public.p4_domain_cs using hnsw (embedding extensions.vector_cosine_ops);
create index if not exists p4_domain_aiml_vec_idx
  on public.p4_domain_aiml using hnsw (embedding extensions.vector_cosine_ops);

-- FTS indexes retained for future hybrid retrieval parity with bdw_chunks.
create index if not exists p4_domain_math_tsv_idx
  on public.p4_domain_math using gin (content_tsv);
create index if not exists p4_domain_vlsi_tsv_idx
  on public.p4_domain_vlsi using gin (content_tsv);
create index if not exists p4_domain_embedded_tsv_idx
  on public.p4_domain_embedded using gin (content_tsv);
create index if not exists p4_domain_cs_tsv_idx
  on public.p4_domain_cs using gin (content_tsv);
create index if not exists p4_domain_aiml_tsv_idx
  on public.p4_domain_aiml using gin (content_tsv);

-- Internal-table lockdown (zero-tolerance rule: no anon/authenticated access).
alter table public.p4_domain_math    enable row level security;
alter table public.p4_domain_vlsi    enable row level security;
alter table public.p4_domain_embedded enable row level security;
alter table public.p4_domain_cs      enable row level security;
alter table public.p4_domain_aiml    enable row level security;

revoke all on public.p4_domain_math     from anon, authenticated;
revoke all on public.p4_domain_vlsi     from anon, authenticated;
revoke all on public.p4_domain_embedded from anon, authenticated;
revoke all on public.p4_domain_cs       from anon, authenticated;
revoke all on public.p4_domain_aiml     from anon, authenticated;

grant select, insert, update, delete on public.p4_domain_math     to service_role;
grant select, insert, update, delete on public.p4_domain_vlsi     to service_role;
grant select, insert, update, delete on public.p4_domain_embedded to service_role;
grant select, insert, update, delete on public.p4_domain_cs       to service_role;
grant select, insert, update, delete on public.p4_domain_aiml     to service_role;

-- ---------------------------------------------------------------------------
-- 2. Seed provenance manifest (one row per domain, written by
--    src/p4_seed_supabase_domains.py).
-- ---------------------------------------------------------------------------
create table if not exists public.p4_domain_index_manifest (
  domain               text primary key
                       check (domain in ('math','vlsi','embedded','cs','aiml')),
  embedder             text not null,
  dim                  int  not null check (dim = 384),
  n                    int  not null,
  built_at             timestamptz,
  source_manifest_md5  text,
  seeded_at            timestamptz not null default now(),
  notes                text
);

alter table public.p4_domain_index_manifest enable row level security;
revoke all on public.p4_domain_index_manifest from anon, authenticated;
grant select, insert, update, delete on public.p4_domain_index_manifest
  to service_role;

-- ---------------------------------------------------------------------------
-- 3. Retrieval RPCs (one per table; SECURITY DEFINER, service_role only).
--    Shape matches what DomainHybridRetriever expects: id/title/source_url/
--    content/similarity, similarity = 1 - cosine_distance.
-- ---------------------------------------------------------------------------
create or replace function public.match_p4_math_chunks(
  query_embedding extensions.vector(384),
  match_count int default 8,
  min_similarity double precision default 0.0)
returns table (id text, title text, source_url text, content text,
               similarity double precision)
language sql stable security definer set search_path = ''
as $$
  select t.id, t.title, t.source_url, t.content, t.similarity
  from (
    select c.id, c.title, c.source_url, c.content,
           1 - (c.embedding operator(extensions.<=>) query_embedding)
             as similarity
    from public.p4_domain_math c
    order by c.embedding operator(extensions.<=>) query_embedding
    limit greatest(match_count, 1)
  ) t
  where t.similarity >= min_similarity;
$$;

create or replace function public.match_p4_vlsi_chunks(
  query_embedding extensions.vector(384),
  match_count int default 8,
  min_similarity double precision default 0.0)
returns table (id text, title text, source_url text, content text,
               similarity double precision)
language sql stable security definer set search_path = ''
as $$
  select t.id, t.title, t.source_url, t.content, t.similarity
  from (
    select c.id, c.title, c.source_url, c.content,
           1 - (c.embedding operator(extensions.<=>) query_embedding)
             as similarity
    from public.p4_domain_vlsi c
    order by c.embedding operator(extensions.<=>) query_embedding
    limit greatest(match_count, 1)
  ) t
  where t.similarity >= min_similarity;
$$;

create or replace function public.match_p4_embedded_chunks(
  query_embedding extensions.vector(384),
  match_count int default 8,
  min_similarity double precision default 0.0)
returns table (id text, title text, source_url text, content text,
               similarity double precision)
language sql stable security definer set search_path = ''
as $$
  select t.id, t.title, t.source_url, t.content, t.similarity
  from (
    select c.id, c.title, c.source_url, c.content,
           1 - (c.embedding operator(extensions.<=>) query_embedding)
             as similarity
    from public.p4_domain_embedded c
    order by c.embedding operator(extensions.<=>) query_embedding
    limit greatest(match_count, 1)
  ) t
  where t.similarity >= min_similarity;
$$;

create or replace function public.match_p4_cs_chunks(
  query_embedding extensions.vector(384),
  match_count int default 8,
  min_similarity double precision default 0.0)
returns table (id text, title text, source_url text, content text,
               similarity double precision)
language sql stable security definer set search_path = ''
as $$
  select t.id, t.title, t.source_url, t.content, t.similarity
  from (
    select c.id, c.title, c.source_url, c.content,
           1 - (c.embedding operator(extensions.<=>) query_embedding)
             as similarity
    from public.p4_domain_cs c
    order by c.embedding operator(extensions.<=>) query_embedding
    limit greatest(match_count, 1)
  ) t
  where t.similarity >= min_similarity;
$$;

create or replace function public.match_p4_aiml_chunks(
  query_embedding extensions.vector(384),
  match_count int default 8,
  min_similarity double precision default 0.0)
returns table (id text, title text, source_url text, content text,
               similarity double precision)
language sql stable security definer set search_path = ''
as $$
  select t.id, t.title, t.source_url, t.content, t.similarity
  from (
    select c.id, c.title, c.source_url, c.content,
           1 - (c.embedding operator(extensions.<=>) query_embedding)
             as similarity
    from public.p4_domain_aiml c
    order by c.embedding operator(extensions.<=>) query_embedding
    limit greatest(match_count, 1)
  ) t
  where t.similarity >= min_similarity;
$$;

-- RPC privileges: service_role only (anon/authenticated intentionally omitted).
grant execute on function
  public.match_p4_math_chunks(extensions.vector, int, double precision)
  to service_role;
grant execute on function
  public.match_p4_vlsi_chunks(extensions.vector, int, double precision)
  to service_role;
grant execute on function
  public.match_p4_embedded_chunks(extensions.vector, int, double precision)
  to service_role;
grant execute on function
  public.match_p4_cs_chunks(extensions.vector, int, double precision)
  to service_role;
grant execute on function
  public.match_p4_aiml_chunks(extensions.vector, int, double precision)
  to service_role;

-- ---------------------------------------------------------------------------
-- 4. Ops comments
-- ---------------------------------------------------------------------------
comment on table public.p4_domain_math is
  'Phase 4 math domain RAG chunks (bge-small-en-v1.5 384d); internal, service_role only';
comment on table public.p4_domain_vlsi is
  'Phase 4 vlsi domain RAG chunks (bge-small-en-v1.5 384d); internal, service_role only';
comment on table public.p4_domain_embedded is
  'Phase 4 embedded domain RAG chunks (bge-small-en-v1.5 384d); internal, service_role only';
comment on table public.p4_domain_cs is
  'Phase 4 cs domain RAG chunks (bge-small-en-v1.5 384d); internal, service_role only';
comment on table public.p4_domain_aiml is
  'Phase 4 aiml domain RAG chunks (bge-small-en-v1.5 384d); internal, service_role only';
comment on table public.p4_domain_index_manifest is
  'Phase 4 domain index provenance (local idx_<domain> build -> Supabase seed)';
