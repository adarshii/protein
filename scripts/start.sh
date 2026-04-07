#!/bin/bash
set -e

echo "Starting BioChemAI Platform..."

# Check if docker-compose available
if command -v docker-compose >/dev/null 2>&1; then
    docker-compose up -d postgres redis neo4j rabbitmq
    echo "Infrastructure services started"
fi

# Start backend
cd backend
source venv/bin/activate 2>/dev/null || true
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
echo "Backend started (PID: $BACKEND_PID)"
cd ..

# Start frontend
cd frontend
npm run dev &
FRONTEND_PID=$!
echo "Frontend started (PID: $FRONTEND_PID)"
cd ..

echo ""
echo "BioChemAI Platform running:"
echo "  Backend:  http://localhost:8000"
echo "  Frontend: http://localhost:3000"
echo "  API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"

wait
