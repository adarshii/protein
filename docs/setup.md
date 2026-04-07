# Setup Guide

## Prerequisites

| Tool | Minimum Version | Notes |
|---|---|---|
| Python | 3.11+ | Used for the FastAPI backend |
| Node.js | 20+ | Used for the Next.js frontend |
| Docker | 24+ | Required for infrastructure services (Postgres, Redis, Neo4j, RabbitMQ) |
| npm | 9+ | Bundled with Node 20 |

Verify your versions:

```bash
python3 --version
node --version
docker --version
```

---

## Development Setup

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/biochemai.git
cd biochemai
```

### 2. Environment Variables

Copy the example env file and fill in your values:

```bash
cp .env.example .env
```

Key variables to configure (see [Deployment](deployment.md) for the full reference):

```
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/biochemai
REDIS_URL=redis://localhost:6379
SECRET_KEY=<generate with: python3 -c "import secrets; print(secrets.token_hex(32))">
JWT_SECRET=<generate with: python3 -c "import secrets; print(secrets.token_hex(32))">
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. Backend Setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate          # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cd ..
```

### 4. Frontend Setup

```bash
cd frontend
npm install
cd ..
```

Or use the automated script:

```bash
chmod +x scripts/setup.sh
./scripts/setup.sh
```

---

## Running with Docker Compose

Start all infrastructure services and the full application stack:

```bash
docker-compose up --build
```

This starts:
- **PostgreSQL** on port 5432
- **Redis** on port 6379
- **Neo4j** on ports 7474 (HTTP) and 7687 (Bolt)
- **RabbitMQ** on port 5672 (management UI on 15672)
- **Backend** (FastAPI) on port 8000
- **Frontend** (Next.js) on port 3000

---

## Running Locally (without Docker)

Start infrastructure services only:

```bash
docker-compose up -d postgres redis neo4j rabbitmq
```

Start the backend:

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Start the frontend (in a separate terminal):

```bash
cd frontend
npm run dev
```

Or use the convenience script:

```bash
./scripts/start.sh
```

Services will be available at:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs (Swagger)**: http://localhost:8000/docs
- **API Docs (ReDoc)**: http://localhost:8000/redoc

---

## Testing

### Backend

```bash
cd backend
source venv/bin/activate
pytest --cov=app --cov-report=term-missing -v
```

### Frontend

```bash
cd frontend
npm run type-check
npm run lint
npm run build
```

### All Tests at Once

```bash
./scripts/test.sh
```
