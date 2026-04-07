#!/bin/bash
set -e

echo "Setting up BioChemAI Platform..."

# Check prerequisites
command -v python3 >/dev/null 2>&1 || { echo "Python 3 required"; exit 1; }
command -v node >/dev/null 2>&1 || { echo "Node.js required"; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "Docker required"; exit 1; }

# Copy env file
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env from .env.example - please update with your values"
fi

# Backend setup
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ..

# Frontend setup
cd frontend
npm install
cd ..

echo "Setup complete! Run ./scripts/start.sh to start the development environment."
