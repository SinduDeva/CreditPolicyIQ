#!/bin/bash

# Credit Policy Automation Tool - Complete Startup Script
# Starts both FastAPI backend and Streamlit frontend

set -e

echo "=========================================="
echo "CreditPolicyIQ - Complete Setup & Start"
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
    echo "⚠️  Configuration file not found"
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "✅ .env file created"
    echo "⚠️  Please update .env with your Anthropic API key:"
    echo "   ANTHROPIC_API_KEY=your-key-here"
    echo ""
fi

# Load environment variables
if [ -f ".env" ]; then
    echo "📄 Loading environment variables from .env..."
    set -a
    source .env
    set +a
fi

# Validate API key
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "❌ Error: ANTHROPIC_API_KEY not configured"
    echo "Please set it in .env file"
    exit 1
fi

echo "✅ Configuration validated"
echo ""

# Create data directories
echo "📁 Creating data directories..."
mkdir -p data/changes
mkdir -p data/metadata
mkdir -p data/cache
mkdir -p data/uploads
mkdir -p logs
echo "✅ Data directories ready"
echo ""

# Make scripts executable
chmod +x run_backend.sh run_frontend.sh

echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "Starting services..."
echo ""

# Start backend in background
echo "1️⃣  Starting FastAPI backend on port 8000..."
python3 app.py &
BACKEND_PID=$!
echo "   Backend PID: $BACKEND_PID"
echo ""

# Wait for backend to start
sleep 2

# Start frontend
echo "2️⃣  Starting Streamlit dashboard on port 8501..."
echo ""

trap "kill $BACKEND_PID" EXIT

streamlit run streamlit_app.py
