#!/bin/bash

# Credit Policy Automation Tool - Backend Startup Script
# Starts FastAPI backend server

set -e

echo "=========================================="
echo "CreditPolicyIQ - FastAPI Backend"
echo "=========================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed"
    echo "Please install Python 3.9 or higher"
    exit 1
fi

echo "✅ Python version:"
python3 --version
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
    echo ""
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/bin/activate
echo "✅ Virtual environment activated"
echo ""

# Install/upgrade dependencies
echo "📥 Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo "✅ Dependencies installed"
echo ""

# Check for .env file
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found"
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "⚠️  Please update .env with your configuration"
    echo ""
fi

# Create data directories
echo "📁 Creating data directories..."
mkdir -p data/changes
mkdir -p data/metadata
mkdir -p data/cache
mkdir -p data/uploads
mkdir -p logs
echo "✅ Data directories ready"
echo ""

# Load environment variables
if [ -f ".env" ]; then
    echo "📄 Loading environment variables from .env..."
    set -a
    source .env
    set +a
fi

# Check for API key
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "❌ Error: ANTHROPIC_API_KEY not set"
    echo "Please set it in .env file or export it:"
    echo "export ANTHROPIC_API_KEY='your-key-here'"
    exit 1
fi

echo "✅ API key configured"
echo ""

# Start backend
echo "🚀 Starting FastAPI backend server..."
echo ""
echo "Backend running at: http://localhost:8000"
echo "API Docs available at: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python3 app.py
