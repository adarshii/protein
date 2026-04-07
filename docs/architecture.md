# Architecture

## Overview

BioChemAI is a microservice-style monorepo platform for bioinformatics and cheminformatics workloads. A Next.js frontend communicates with a single FastAPI backend that aggregates domain-specific service modules (bio, chem, ml, genomics). Shared infrastructure (PostgreSQL, Redis, Neo4j, RabbitMQ) is managed via Docker Compose for local development and separate managed services in production.

```
┌─────────────────────────────────────────────────────────────────┐
│                          Client Browser                         │
└──────────────────────────────┬──────────────────────────────────┘
                               │ HTTPS
┌──────────────────────────────▼──────────────────────────────────┐
│                    Next.js Frontend (Vercel)                     │
│           React · TypeScript · Tailwind CSS · ShadCN            │
└──────────────────────────────┬──────────────────────────────────┘
                               │ REST / JSON
┌──────────────────────────────▼──────────────────────────────────┐
│                   FastAPI Backend (Render)                       │
│  ┌────────────┬─────────────┬────────────────┬────────────────┐ │
│  │ /bio       │ /chem       │ /ml            │ /genomics      │ │
│  │ Protein    │ Molecule    │ Model          │ Sequence       │ │
│  │ Analysis   │ Properties  │ Inference      │ Analysis       │ │
│  └─────┬──────┴──────┬──────┴───────┬────────┴───────┬────────┘ │
└────────│─────────────│──────────────│────────────────│──────────┘
         │             │              │                │
   ┌─────▼──────┐ ┌────▼─────┐ ┌─────▼──────┐ ┌──────▼─────┐
   │ PostgreSQL │ │  Redis   │ │   Neo4j    │ │ RabbitMQ   │
   │ (primary   │ │ (cache + │ │ (graph DB  │ │ (async     │
   │  storage)  │ │  queue)  │ │  biology)  │ │  tasks)    │
   └────────────┘ └──────────┘ └────────────┘ └────────────┘
```

---

## Components

### Frontend (Next.js)

- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS + ShadCN UI components
- **State**: React Query for server state; Zustand for client state
- **Auth**: JWT tokens stored in httpOnly cookies

### Backend (FastAPI)

- **Framework**: FastAPI with async/await throughout
- **Language**: Python 3.11
- **ORM**: SQLAlchemy 2.0 (async) with Alembic migrations
- **Auth**: OAuth2 password flow + JWT (python-jose)
- **Task Queue**: Celery workers consuming RabbitMQ
- **Validation**: Pydantic v2 models

### Service Modules

| Module | Responsibility |
|---|---|
| `app/bio` | Protein structure prediction, BLAST search, sequence alignment |
| `app/chem` | Molecular property calculation, SMILES parsing, drug-likeness scoring |
| `app/ml` | ML model registry, inference endpoints, result caching |
| `app/genomics` | Genome sequence analysis, variant calling pipeline integration |

### Infrastructure

| Service | Purpose | Port |
|---|---|---|
| PostgreSQL 15 | Relational data (users, jobs, results) | 5432 |
| Redis 7 | Response caching, Celery broker/backend | 6379 |
| Neo4j 5 | Protein interaction networks, pathway graphs | 7474 / 7687 |
| RabbitMQ 3 | Long-running job queue | 5672 / 15672 |

---

## Data Flow

### Synchronous Request (e.g. molecular property lookup)

```
Browser → Next.js → FastAPI /chem/properties → Redis cache hit? → return
                                              → cache miss → compute → cache → return
```

### Asynchronous Job (e.g. protein structure prediction)

```
Browser → Next.js → FastAPI /bio/predict → enqueue RabbitMQ task → return job_id
Browser → poll FastAPI /jobs/{job_id}    → Redis status check
Celery worker → compute result → write PostgreSQL → update Redis status
Browser → poll returns "complete"        → fetch result from FastAPI
```

---

## Technology Choices and Rationale

| Choice | Rationale |
|---|---|
| FastAPI | Native async support, automatic OpenAPI docs, Pydantic validation |
| Next.js App Router | Server components reduce client bundle; streaming for long AI responses |
| PostgreSQL | ACID compliance for job records; JSONB for flexible result storage |
| Redis | Sub-millisecond cache for repeated computations; Celery broker |
| Neo4j | Graph queries for protein–protein interaction networks outperform relational joins |
| RabbitMQ | Durable task queues for expensive ML inference jobs |
| Docker Compose | Reproducible local environment matching production topology |

---

## Database Schema Overview

```
users
  id            UUID PK
  email         TEXT UNIQUE
  hashed_pw     TEXT
  created_at    TIMESTAMPTZ

jobs
  id            UUID PK
  user_id       UUID FK → users.id
  service       TEXT          -- bio | chem | ml | genomics
  status        TEXT          -- queued | running | complete | failed
  payload       JSONB
  result        JSONB
  created_at    TIMESTAMPTZ
  updated_at    TIMESTAMPTZ

molecules
  id            UUID PK
  smiles        TEXT
  inchi_key     TEXT UNIQUE
  properties    JSONB
  created_at    TIMESTAMPTZ

sequences
  id            UUID PK
  accession     TEXT UNIQUE
  sequence      TEXT
  organism      TEXT
  metadata      JSONB
  created_at    TIMESTAMPTZ
```
