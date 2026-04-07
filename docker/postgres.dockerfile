# ============================================================
# Custom PostgreSQL 15 image for BioChemAI
# Includes: pg_trgm, uuid-ossp extensions + init SQL scripts
# ============================================================
FROM postgres:15-alpine

LABEL maintainer="BioChemAI Platform" \
      description="PostgreSQL 15 with BioChemAI schema initialization"

# Install additional utilities useful for debugging
RUN apk add --no-cache \
    curl \
    bash

# Copy initialization scripts; these run in alphabetical order on first start
COPY initdb/ /docker-entrypoint-initdb.d/

# Custom postgresql.conf overrides for performance tuning
COPY postgresql.conf /etc/postgresql/postgresql.conf

# Expose standard Postgres port
EXPOSE 5432

# Use our custom config file
CMD ["postgres", "-c", "config_file=/etc/postgresql/postgresql.conf"]
