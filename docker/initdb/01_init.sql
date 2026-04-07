-- ============================================================
-- BioChemAI PostgreSQL initialization script
-- Runs automatically on first container start
-- ============================================================

-- Enable essential extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
CREATE EXTENSION IF NOT EXISTS "citext";

-- Create application schema
CREATE SCHEMA IF NOT EXISTS biochemai;

-- Grant privileges to application user (set via POSTGRES_USER env var)
DO $$
DECLARE
    app_user TEXT := current_user;
BEGIN
    EXECUTE format('GRANT ALL PRIVILEGES ON SCHEMA biochemai TO %I', app_user);
    EXECUTE format('ALTER DEFAULT PRIVILEGES IN SCHEMA biochemai GRANT ALL ON TABLES TO %I', app_user);
    EXECUTE format('ALTER DEFAULT PRIVILEGES IN SCHEMA biochemai GRANT ALL ON SEQUENCES TO %I', app_user);
END
$$;

-- Baseline audit log table (Alembic migrations will create domain tables)
CREATE TABLE IF NOT EXISTS biochemai.schema_info (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    key         CITEXT UNIQUE NOT NULL,
    value       TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO biochemai.schema_info (key, value)
VALUES ('initialized_at', NOW()::TEXT)
ON CONFLICT (key) DO NOTHING;
