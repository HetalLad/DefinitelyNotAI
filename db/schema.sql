-- AskWRI tables and indexes on askwri-db. Safe to rerun: python3 db/apply_schema.py
-- Statements end with ";" at the end of a line; the apply script splits on that.

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS documents (
  doc_id text PRIMARY KEY,            -- wri.org URL, else the DOI, else the file's SHA-256
  url text,
  doi text,
  file_sha256 text UNIQUE NOT NULL,   -- always stored, to catch the same PDF arriving twice
  title text,
  year int,
  pub_date date,
  date_source text CHECK (date_source IN ('manifest', 'printed', 'file_metadata', 'none')),
  date_confidence text CHECK (date_confidence IN ('high', 'low', 'undated')),
  pub_type text,
  office text,
  program text,
  countries text[],
  regions text[],
  topics text[],
  authors text[],
  language text
);

CREATE TABLE IF NOT EXISTS chunks (
  chunk_id text PRIMARY KEY,          -- "<doc_id>#p<page>-<position on page>"
  doc_id text NOT NULL REFERENCES documents(doc_id) ON DELETE CASCADE,
  page int NOT NULL,
  section text,
  content text NOT NULL,
  is_table_or_figure boolean NOT NULL DEFAULT false,
  quotable boolean NOT NULL DEFAULT true,  -- false: cite the page, never quote verbatim
  embedding vector(1024),             -- must equal the embedding_dim Terraform variable
  tsv tsvector GENERATED ALWAYS AS (to_tsvector('simple', content)) STORED
);

CREATE INDEX IF NOT EXISTS chunks_embedding_idx ON chunks USING hnsw (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS chunks_tsv_idx ON chunks USING gin (tsv);
CREATE INDEX IF NOT EXISTS chunks_doc_id_idx ON chunks (doc_id);
CREATE INDEX IF NOT EXISTS documents_filters_idx ON documents (year, pub_type, program, language);

CREATE TABLE IF NOT EXISTS translations (
  hash text PRIMARY KEY,              -- SHA-256 of target language + source text
  lang text NOT NULL,
  text text NOT NULL
);

-- App users sign in with IAM database authentication, so no app password exists anywhere.
DO $$ BEGIN CREATE ROLE askwri_ingest LOGIN; EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE ROLE askwri_tools LOGIN; EXCEPTION WHEN duplicate_object THEN NULL; END $$;
GRANT rds_iam TO askwri_ingest, askwri_tools;

GRANT SELECT, INSERT, UPDATE, DELETE ON documents, chunks TO askwri_ingest;
GRANT SELECT ON documents, chunks TO askwri_tools;
GRANT SELECT, INSERT, UPDATE ON translations TO askwri_tools;
