# Deployment

## Render (Backend)

The backend is configured for Render via `render.yaml` in the repository root.

### Manual Setup

1. Create a new **Web Service** in Render and connect your GitHub repository.
2. Set the following:
   - **Runtime**: Docker
   - **Dockerfile**: `Dockerfile.backend`
   - **Root Directory**: `.` (repository root)
3. Add all required environment variables (see [Environment Variables](#environment-variables) below).
4. Click **Deploy**.

Render will automatically deploy on every push to `main`.

### Database

Create a **PostgreSQL** managed database in Render and copy the internal connection string into `DATABASE_URL`.

---

## Vercel (Frontend)

The frontend is configured for Vercel via `vercel.json` in the repository root.

### Manual Setup

1. Import the repository in the [Vercel dashboard](https://vercel.com/new).
2. Set **Framework Preset** to `Next.js`.
3. Set **Root Directory** to `frontend`.
4. Add `NEXT_PUBLIC_API_URL` pointing to your Render backend URL.
5. Click **Deploy**.

Vercel deploys automatically on push to `main` and creates preview deployments for pull requests.

---

## Docker Production Deployment

Build and start the full stack with a single command:

```bash
docker-compose -f docker-compose.yml up --build -d
```

### Build Individual Images

```bash
# Backend
docker build -f Dockerfile.backend -t biochemai-backend:latest .

# Frontend
docker build -f Dockerfile.frontend -t biochemai-frontend:latest frontend/
```

### Run Without Compose

```bash
# Start infrastructure
docker network create biochemai
docker run -d --name postgres --network biochemai \
  -e POSTGRES_DB=biochemai -e POSTGRES_USER=user -e POSTGRES_PASSWORD=password \
  postgres:15

docker run -d --name redis --network biochemai redis:7

# Start backend
docker run -d --name backend --network biochemai -p 8000:8000 \
  --env-file .env biochemai-backend:latest

# Start frontend
docker run -d --name frontend --network biochemai -p 3000:3000 \
  -e NEXT_PUBLIC_API_URL=http://localhost:8000 biochemai-frontend:latest
```

---

## Environment Variables Reference

### Backend

| Variable | Required | Description | Example |
|---|---|---|---|
| `DATABASE_URL` | ✅ | Async PostgreSQL connection string | `postgresql+asyncpg://user:pass@host/db` |
| `REDIS_URL` | ✅ | Redis connection string | `redis://localhost:6379` |
| `SECRET_KEY` | ✅ | Application secret (32+ random bytes) | `openssl rand -hex 32` |
| `JWT_SECRET` | ✅ | JWT signing secret (32+ random bytes) | `openssl rand -hex 32` |
| `JWT_ALGORITHM` | ❌ | JWT algorithm (default: `HS256`) | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | ❌ | Token TTL in minutes (default: `60`) | `60` |
| `RABBITMQ_URL` | ❌ | RabbitMQ AMQP URL | `amqp://guest:guest@localhost/` |
| `NEO4J_URI` | ❌ | Neo4j bolt URI | `bolt://localhost:7687` |
| `NEO4J_USER` | ❌ | Neo4j username | `neo4j` |
| `NEO4J_PASSWORD` | ❌ | Neo4j password | `password` |
| `CORS_ORIGINS` | ❌ | Comma-separated allowed origins | `https://biochemai.vercel.app` |
| `LOG_LEVEL` | ❌ | Log level (default: `INFO`) | `INFO` |

### Frontend

| Variable | Required | Description | Example |
|---|---|---|---|
| `NEXT_PUBLIC_API_URL` | ✅ | Backend API base URL | `https://biochemai-api.onrender.com` |

---

## Monitoring and Logging

### Health Checks

| Endpoint | Description |
|---|---|
| `GET /health` | Returns `{"status": "ok"}` when the API is healthy |
| `GET /health/db` | Checks PostgreSQL connectivity |
| `GET /health/redis` | Checks Redis connectivity |

### Logs

**Backend** logs are written to stdout in JSON format and are collected automatically by Render and Docker logging drivers.

**Frontend** logs are available in the Vercel dashboard under **Deployments → Functions**.

### Recommended Monitoring Stack

| Tool | Purpose |
|---|---|
| [Sentry](https://sentry.io) | Error tracking (add `SENTRY_DSN` env var) |
| [Prometheus + Grafana](https://grafana.com) | Metrics via `/metrics` endpoint (FastAPI Prometheus middleware) |
| [Uptime Robot](https://uptimerobot.com) | Uptime monitoring on `/health` |

To enable Sentry in the backend, set:

```
SENTRY_DSN=https://<key>@<org>.ingest.sentry.io/<project>
```
