#!/bin/bash
set -e

echo "Running all tests..."

# Backend tests
echo "=== Backend Tests ==="
cd backend
source venv/bin/activate 2>/dev/null || true
pytest --cov=app --cov-report=term-missing -v
cd ..

# Frontend tests
echo "=== Frontend Tests ==="
cd frontend
npm run type-check
npm run lint
cd ..

echo "All tests passed!"
