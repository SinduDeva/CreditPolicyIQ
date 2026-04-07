#!/bin/bash

# Credit Policy Automation Tool - Complete Startup Script
# Starts both FastAPI backend and Streamlit frontend

set -e

echo "=========================================="
echo "CreditPolicyIQ - Complete Setup & Start"
echo "=========================================="
echo ""

# Find Python executable (try python3 first, fallback to python)
PYTHON_CMD=""
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
fi

if [ -z "$PYTHON_CMD" ]; then
    echo "❌ Error: Python is not installed or not in PATH"
    echo "Please install Python 3.9 or higher"
    echo ""
    echo "Installation options:"
    echo "  • Ubuntu/Debian: sudo apt-get install python3"
    echo "  • macOS: brew install python3"
    echo "  • Windows: Download from https://python.org/"
    exit 1
fi

echo "✅ Python found:"
$PYTHON_CMD --version
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    $PYTHON_CMD -m venv venv
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
    echo ""
    echo "📝 Configuration options:"
    echo "   • Default: Mock provider (works without API key)"
    echo "   • Optional: Add LLM_API_KEY for Anthropic or OpenAI"
    echo "   • Edit .env to configure your preferred provider"
    echo ""
fi

# Load environment variables
if [ -f ".env" ]; then
    echo "📄 Loading environment variables from .env..."
    set -a
    source .env
    set +a
fi

# Determine LLM configuration
if [ -z "$LLM_PROVIDER" ]; then
    LLM_PROVIDER="mock"
    echo "📢 LLM_PROVIDER not set, defaulting to: mock (no API key needed)"
fi

if [ -z "$LLM_API_KEY" ] && [ -n "$ANTHROPIC_API_KEY" ]; then
    LLM_API_KEY="$ANTHROPIC_API_KEY"
    echo "📢 Using ANTHROPIC_API_KEY for compatibility"
fi

echo "✅ Configuration loaded (Provider: $LLM_PROVIDER)"
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
# Use bash -c to ensure venv is active in the background process
bash -c "source venv/bin/activate && python3 app.py" &
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
