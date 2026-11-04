-- Phase 3 P3.1 — retrieval RPCs for the e2e test and the Zone 2 gateway
-- (PHASE3_INTEGRATION_BLUEPRINT.md, BDW_INTEGRATION.md section 7.2 hybrid).
-- Owner applies via Supabase SQL editor or psql; idempotent.
-- SECURITY DEFINER is required because bdw_chunks is RLS-protected and the
-- gateway calls these through the service role; search_path is pinned.

create or replace function public.match_chunks_vec(
  query_embedding extensions.vector(384),
  match_count int default 8,
  verified_only boolean default false)
returns table (
  id uuid, parent_type text, parent_id uuid, source_url text,
  title text, content text, similarity double precision)
language sql stable security definer set search_path = ''
as $$
  select c.id, c.parent_type, c.parent_id, c.source_url,
         c.title, c.content,
         1 - (c.embedding operator(extensions.<=>) query_embedding) as similarity
  from public.bdw_chunks c
  where (not verified_only) or c.verified
  order by c.embedding operator(extensions.<=>) query_embedding
  limit greatest(match_count, 1);
$$;

create or replace function public.match_chunks_fts(
  query text,
  match_count int default 8,
  verified_only boolean default false)
returns table (
  id uuid, parent_type text, parent_id uuid, source_url text,
  title text, content text, rank double precision)
language sql stable security definer set search_path = ''
as $$
  select c.id, c.parent_type, c.parent_id, c.source_url,
         c.title, c.content,
         ts_rank(c.content_tsv, websearch_to_tsquery('english', query))
           ::double precision as rank
  from public.bdw_chunks c
  where c.content_tsv @@ websearch_to_tsquery('english', query)
    and ((not verified_only) or c.verified)
  order by rank desc
  limit greatest(match_count, 1);
$$;

grant execute on function public.match_chunks_vec(extensions.vector, int, boolean)
  to service_role;
grant execute on function public.match_chunks_fts(text, int, boolean)
  to service_role;

-- audit note: anon/authenticated grants are intentionally NOT added;
-- retrieval goes through the Zone 2 gateway only (S1/S5).
