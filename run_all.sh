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

# Detect OS and activate appropriately
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" || "$OSTYPE" == "cygwin" ]]; then
    # Windows (Git Bash, MSYS, Cygwin)
    if [ -f "venv/Scripts/activate" ]; then
        source venv/Scripts/activate
    else
        echo "❌ Error: Virtual environment activation script not found"
        echo "   Expected: venv/Scripts/activate"
        echo "   Check if venv directory exists: $(ls -la venv 2>/dev/null || echo 'NOT FOUND')"
        exit 1
    fi
elif [ -f "venv/bin/activate" ]; then
    # Unix-like systems (macOS, Linux)
    source venv/bin/activate
else
    echo "❌ Error: Virtual environment activation script not found"
    echo "   Expected: venv/bin/activate"
    echo "   Check if venv directory exists: $(ls -la venv 2>/dev/null || echo 'NOT FOUND')"
    exit 1
fi

echo "✅ Virtual environment activated"
echo ""

# Install/upgrade dependencies
echo "📥 Installing dependencies..."

# Try to upgrade pip (non-critical, continue if fails)
echo "   Checking pip version..."
pip install --upgrade pip 2>/dev/null || {
    echo "   ⚠️  Pip upgrade skipped (using current version)"
}

# Install requirements
echo "   Installing packages from requirements.txt..."
pip install -r requirements.txt || {
    echo "❌ Error: Failed to install dependencies"
    echo "   Please check your internet connection and try again"
    exit 1
}

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

# Determine correct activation script for OS
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" || "$OSTYPE" == "cygwin" ]]; then
    # Windows
    ACTIVATE_CMD="source venv/Scripts/activate && python app.py"
else
    # Unix-like (macOS, Linux)
    ACTIVATE_CMD="source venv/bin/activate && python app.py"
fi

# Use bash -c to ensure venv is active in the background process
bash -c "$ACTIVATE_CMD" &
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
