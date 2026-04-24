-- =============================================================================
-- KnowShift: Temporal Self-Healing RAG System
-- Supabase Schema — Phase 1
-- =============================================================================

-- Enable pgvector extension for semantic similarity search
CREATE EXTENSION IF NOT EXISTS vector;

-- =============================================================================
-- TABLE: documents
-- Stores metadata about each ingested source document.
-- =============================================================================
CREATE TABLE IF NOT EXISTS documents (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    domain           TEXT NOT NULL CHECK (domain IN ('medical', 'finance', 'ai_policy')),
    source_url       TEXT,                                       -- nullable: not all docs have a URL
    source_name      TEXT NOT NULL,                             -- human-readable name of the source
    published_at     TIMESTAMPTZ,                               -- nullable: original publication date
    last_verified    TIMESTAMPTZ NOT NULL DEFAULT NOW(),        -- when we last verified freshness
    validity_horizon INTEGER NOT NULL DEFAULT 365,              -- days until considered stale
    stale_flag       BOOLEAN NOT NULL DEFAULT FALSE,            -- TRUE when past validity_horizon
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for fast domain-filtered lookups
CREATE INDEX IF NOT EXISTS idx_documents_domain
    ON documents (domain);

-- Index for staleness sweeps (sorted by last_verified)
CREATE INDEX IF NOT EXISTS idx_documents_last_verified
    ON documents (last_verified);

-- =============================================================================
-- TABLE: chunks
-- Stores text chunks with their 768-dim Gemini embeddings and freshness state.
-- =============================================================================
CREATE TABLE IF NOT EXISTS chunks (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id      UUID NOT NULL REFERENCES documents (id) ON DELETE CASCADE,
    chunk_text       TEXT NOT NULL,                             -- raw chunk content
    embedding        VECTOR(768),                               -- Gemini text-embedding-004 output
    freshness_score  FLOAT NOT NULL DEFAULT 1.0,               -- exponential decay score [0, 1]
    is_deprecated    BOOLEAN NOT NULL DEFAULT FALSE,            -- TRUE when superseded by new content
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- IVFFlat ANN index for cosine-distance similarity search
-- lists=100 is a good default for datasets up to ~1M vectors;
-- increase 'probes' at query time for recall vs. speed trade-off.
CREATE INDEX IF NOT EXISTS idx_chunks_embedding
    ON chunks USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- Index for fast document → chunk lookups
CREATE INDEX IF NOT EXISTS idx_chunks_document_id
    ON chunks (document_id);

-- Index for freshness-based filtering
CREATE INDEX IF NOT EXISTS idx_chunks_freshness_score
    ON chunks (freshness_score);

-- =============================================================================
-- TABLE: change_log
-- Audit trail for every mutation the freshness engine performs.
-- =============================================================================
CREATE TABLE IF NOT EXISTS change_log (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chunk_id     UUID REFERENCES chunks (id) ON DELETE SET NULL,
    document_id  UUID REFERENCES documents (id) ON DELETE SET NULL,
    change_type  TEXT NOT NULL CHECK (
                     change_type IN ('deprecated', 'updated', 're-indexed', 'stale_flagged')
                 ),
    reason       TEXT,                                          -- human-readable description
    old_value    TEXT,                                          -- previous value (serialised to TEXT)
    new_value    TEXT,                                          -- new value (serialised to TEXT)
    changed_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for filtering change_log by document
CREATE INDEX IF NOT EXISTS idx_change_log_document_id
    ON change_log (document_id);

-- Index for filtering change_log by chunk
CREATE INDEX IF NOT EXISTS idx_change_log_chunk_id
    ON change_log (chunk_id);

-- Index for time-range queries on audit trail
CREATE INDEX IF NOT EXISTS idx_change_log_changed_at
    ON change_log (changed_at DESC);

-- =============================================================================
-- FUNCTION: match_chunks
-- Primary retrieval function — returns the top-k semantically similar chunks
-- for a given query embedding, with optional domain filtering and stale inclusion.
-- =============================================================================
CREATE OR REPLACE FUNCTION match_chunks(
    query_embedding    VECTOR(768),
    domain_filter      TEXT,
    match_count        INT     DEFAULT 10,
    include_stale      BOOLEAN DEFAULT FALSE
)
RETURNS TABLE (
    chunk_id       UUID,
    chunk_text     TEXT,
    freshness_score FLOAT,
    similarity     FLOAT,
    published_at   TIMESTAMPTZ,
    last_verified  TIMESTAMPTZ,
    source_name    TEXT,
    document_id    UUID
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.id                                    AS chunk_id,
        c.chunk_text,
        c.freshness_score,
        -- Convert cosine *distance* → cosine *similarity* (range: -1 to +1, higher is more similar)
        (1.0 - (c.embedding <=> query_embedding))::FLOAT AS similarity,
        d.published_at,
        d.last_verified,
        d.source_name,
        d.id                                    AS document_id
    FROM chunks c
    JOIN documents d ON c.document_id = d.id
    WHERE
        d.domain = domain_filter
        AND c.is_deprecated = FALSE
        -- When include_stale=FALSE, only return chunks whose document is fresh
        AND (include_stale OR d.stale_flag = FALSE)
    ORDER BY
        c.embedding <=> query_embedding   -- ascending cosine distance = descending similarity
    LIMIT match_count;
END;
$$;

-- =============================================================================
-- FUNCTION: find_overlapping_chunks
-- Used during re-indexing: identifies existing chunks that are semantically
-- close to a candidate new chunk so we can avoid redundant duplicates and
-- selectively deprecate overlapping stale content.
-- =============================================================================
CREATE OR REPLACE FUNCTION find_overlapping_chunks(
    query_embedding      VECTOR(768),
    domain_filter        TEXT,
    similarity_threshold FLOAT   DEFAULT 0.85,
    exclude_doc_id       UUID    DEFAULT NULL
)
RETURNS TABLE (
    chunk_id   UUID,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.id                                                         AS chunk_id,
        (1.0 - (c.embedding <=> query_embedding))::FLOAT             AS similarity
    FROM chunks c
    JOIN documents d ON c.document_id = d.id
    WHERE
        d.domain = domain_filter
        AND c.is_deprecated = FALSE
        -- Optionally exclude a specific document (e.g., the document being re-indexed)
        AND (exclude_doc_id IS NULL OR d.id <> exclude_doc_id)
        -- Only return chunks above the similarity threshold
        AND (1.0 - (c.embedding <=> query_embedding)) >= similarity_threshold
    ORDER BY similarity DESC;
END;
$$;

-- =============================================================================
-- STORAGE BUCKET (run via Supabase Dashboard or Management API)
-- The ingestion pipeline uploads raw PDFs to this bucket.
-- =============================================================================
INSERT INTO storage.buckets (id, name, public)
VALUES ('documents', 'documents', false)
ON CONFLICT (id) DO NOTHING;

-- =============================================================================
-- ROW LEVEL SECURITY
-- Enable RLS on all tables. The backend uses the service-role key which
-- bypasses RLS entirely — these policies protect against accidental anon access.
-- =============================================================================

-- documents
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;

-- Deny all anon/authenticated access (backend uses service-role → bypasses)
CREATE POLICY "deny_anon_documents"
    ON documents
    FOR ALL
    TO anon, authenticated
    USING (false);

-- chunks
ALTER TABLE chunks ENABLE ROW LEVEL SECURITY;

CREATE POLICY "deny_anon_chunks"
    ON chunks
    FOR ALL
    TO anon, authenticated
    USING (false);

-- change_log
ALTER TABLE change_log ENABLE ROW LEVEL SECURITY;

CREATE POLICY "deny_anon_change_log"
    ON change_log
    FOR ALL
    TO anon, authenticated
    USING (false);
