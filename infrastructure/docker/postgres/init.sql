-- ============================================================
-- Lamos Chocolate — PostgreSQL initialization
-- Run once by the postgres image on first container init
-- (the database/user themselves come from POSTGRES_* env vars).
-- ============================================================

-- UUID generation helpers (uuid_generate_v4, ...)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Trigram index support for fuzzy product/category search
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Accent-insensitive search helpers
CREATE EXTENSION IF NOT EXISTS "unaccent";
