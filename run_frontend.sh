#!/bin/bash

# Credit Policy Automation Tool - Streamlit Frontend Startup Script
# Starts Streamlit dashboard

set -e

echo "=========================================="
echo "CreditPolicyIQ - Streamlit Frontend"
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

# Load environment variables
if [ -f ".env" ]; then
    echo "📄 Loading environment variables from .env..."
    set -a
    source .env
    set +a
fi

# Check if backend is running
echo "🔍 Checking if backend is running..."
if ! nc -z localhost 8000 2>/dev/null; then
    echo "⚠️  Warning: Backend server not detected on port 8000"
    echo "Please start the backend first:"
    echo "  ./run_backend.sh"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "✅ Backend server is running"
fi

echo ""

# Start frontend
echo "🚀 Starting Streamlit dashboard..."
echo ""
echo "Dashboard available at: http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

streamlit run streamlit_app.py
