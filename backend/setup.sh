#!/bin/bash

# Backend Setup Script
# This script sets up and runs the Job Search backend

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║       Job Search Backend - Setup & Deploy Script              ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Check Python version
echo "🔍 Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "   Python: $python_version"

# Check if Python 3.11+
if ! python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" 2>/dev/null; then
    echo "❌ Error: Python 3.11 or higher required"
    exit 1
fi

echo "✅ Python version OK"
echo ""

# Install dependencies
echo "📦 Installing dependencies..."
if command -v pip &> /dev/null; then
    echo "   Using pip..."
    pip install -e .
elif command -v uv &> /dev/null; then
    echo "   Using uv (faster)..."
    uv sync
else
    echo "❌ Neither pip nor uv found"
    exit 1
fi
echo "✅ Dependencies installed"
echo ""

# Setup .env file
if [ ! -f ".env" ]; then
    echo "⚙️  Setting up .env file..."
    cp .env.example .env
    echo "✅ .env file created (you can edit it to add GROQ_API_KEY)"
else
    echo "✅ .env file already exists"
fi
echo ""

# Start server
echo "🚀 Starting backend server..."
echo "   Server will run on: http://localhost:8002"
echo "   Web UI: http://localhost:8002"
echo "   Press CTRL+C to stop"
echo ""

uvicorn job_search.api:app --reload --port 8002
