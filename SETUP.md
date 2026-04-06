# CreditPolicyIQ - Local Setup & Deployment Guide

Complete instructions for setting up and running the Credit Policy Automation Tool locally.

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start (5 minutes)](#quick-start)
3. [Detailed Setup](#detailed-setup)
4. [Configuration](#configuration)
5. [Running the Application](#running-the-application)
6. [Testing](#testing)
7. [Troubleshooting](#troubleshooting)
8. [Docker Setup (Optional)](#docker-setup-optional)

---

## Prerequisites

### System Requirements
- **OS**: Linux, macOS, or Windows (with WSL2)
- **Python**: 3.9 or higher
- **RAM**: 4GB minimum
- **Storage**: 500MB for installation + data

### Required Software

```bash
# Check Python version
python3 --version

# Should output: Python 3.9.x or higher
```

### API Key Required
- **Anthropic API Key** - Get it from https://console.anthropic.com/
  - Free trial includes $5 in credits
  - Used for Claude API calls

---

## Quick Start

Get the application running in 5 minutes:

### 1. Clone/Setup Repository
```bash
cd /path/to/CreditPolicyIQ
```

### 2. Configure API Key
```bash
# Copy example configuration
cp .env.example .env

# Edit .env and add your Anthropic API key
# ANTHROPIC_API_KEY=your-api-key-here
```

### 3. Start Application
```bash
# Make scripts executable
chmod +x run_all.sh

# Start both backend and frontend
./run_all.sh
```

### 4. Access Application
- **Dashboard**: http://localhost:8501
- **API Docs**: http://localhost:8000/docs

---

## Detailed Setup

### Step 1: Verify Python Installation

```bash
# Check Python version
python3 --version

# Should be 3.9 or higher
# If not installed, install from https://python.org/

# Verify pip is available
python3 -m pip --version
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
# On Linux/macOS:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install all required packages
pip install -r requirements.txt
```

### Step 4: Create Configuration File

```bash
# Copy example configuration
cp .env.example .env

# Edit .env file
# Uncomment and set:
# - ANTHROPIC_API_KEY=your-key-here
# - Any other custom settings
```

### Step 5: Create Data Directories

```bash
# Create necessary directories
mkdir -p data/changes
mkdir -p data/metadata
mkdir -p data/cache
mkdir -p data/uploads
mkdir -p logs
```

### Step 6: Verify Installation

```bash
# Test Python imports
python3 -c "
from core import ExcelParser, DocxHandler, ChangeDetector, LLMCaller, ApprovalWorkflow
print('✅ All core modules imported successfully')
"

# Test API can start
python3 -c "from app import app; print('✅ FastAPI app loads successfully')"

# Test Streamlit
streamlit hello
```

---

## Configuration

### Environment Variables

Edit `.env` file to configure:

```bash
# === REQUIRED ===
ANTHROPIC_API_KEY=your-api-key-from-anthropic

# === FILE PATHS ===
MASTER_DOCX_PATH=data/master_policy.docx
EXCEL_PATH=data/policy_changes.xlsx

# === LLM SETTINGS ===
LLM_MODEL=claude-3-5-sonnet-20241022
LLM_MAX_TOKENS=1000

# === API SETTINGS ===
API_HOST=0.0.0.0
API_PORT=8000
API_BASE_URL=http://localhost:8000/api

# === LOGGING ===
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
```

### Key Configuration Points

1. **ANTHROPIC_API_KEY** (Required)
   - Get from: https://console.anthropic.com/
   - Must be set for LLM features to work

2. **MASTER_DOCX_PATH**
   - Path to your master credit policy Word document
   - File should exist before uploading Excel changes

3. **LOG_LEVEL**
   - DEBUG: Very verbose (for troubleshooting)
   - INFO: Normal operation
   - WARNING: Warnings and errors only
   - ERROR: Only errors

---

## Running the Application

### Option 1: Run Everything (Recommended)

```bash
# Start both backend and frontend with one command
./run_all.sh

# Output will show:
# 1. Creating/activating virtual environment
# 2. Installing dependencies
# 3. Starting FastAPI backend (port 8000)
# 4. Starting Streamlit dashboard (port 8501)
```

### Option 2: Run Backend Only

```bash
# Terminal 1: Start backend
./run_backend.sh

# Output:
# ✅ FastAPI backend running at: http://localhost:8000
# ✅ API Docs available at: http://localhost:8000/docs
```

### Option 3: Run Frontend Only

```bash
# Terminal 2: Start frontend (requires backend running)
./run_frontend.sh

# Output:
# ✅ Streamlit dashboard running at: http://localhost:8501
```

### Option 4: Manual Setup (Advanced)

```bash
# Activate virtual environment
source venv/bin/activate

# Set environment variables
export ANTHROPIC_API_KEY="your-key"

# Start backend
python3 app.py

# In another terminal:
source venv/bin/activate
streamlit run streamlit_app.py
```

---

## Accessing the Application

### Web Interface (Streamlit Dashboard)
- **URL**: http://localhost:8501
- **Pages**:
  - 📊 Dashboard - Overview and metrics
  - 📤 Upload Excel - Upload policy changes
  - 🔍 Review Changes - Review detected changes
  - ✅ Approve Changes - Approve/reject changes
  - 📄 Master Document - Download and apply changes
  - 📚 Version History - View document versions
  - 📋 Logs - View activity logs

### API Documentation
- **URL**: http://localhost:8000/docs
- **Interactive Swagger UI** for testing endpoints
- **13 RESTful endpoints** for programmatic access

### Health Check
```bash
# Check if backend is running
curl http://localhost:8000/api/health

# Expected response:
# {"status": "healthy"}
```

---

## Testing

### Quick Smoke Test

```bash
# Test backend connectivity
curl http://localhost:8000/api/health

# Test API endpoints
curl http://localhost:8000/api/changes/pending

# Check logs
tail -f logs/app.log
```

### With Sample Data

1. Create sample Excel file:
   - Copy example from docs/
   - Or create new with required columns:
     - Section_ID, Section_Name, Policy_Content
     - UW_Technical_Details, Status, Color_Flag, Notes

2. Create sample master DOCX:
   - Place at `data/master_policy.docx`
   - Any .docx file will work for testing

3. Test workflow:
   - Upload Excel → Review Changes → Approve → Apply Changes

---

## File Structure

```
CreditPolicyIQ/
├── app.py                    # FastAPI backend
├── streamlit_app.py          # Streamlit frontend
├── config.py                 # Configuration management
├── SETUP.md                  # This file
├── README.md                 # Project documentation
├── VALIDATION.md             # Architecture validation
├── requirements.txt          # Python dependencies
├── .env.example              # Configuration template
├── run_backend.sh            # Backend startup script
├── run_frontend.sh           # Frontend startup script
├── run_all.sh                # Complete startup script
│
├── core/                     # Core business logic
│   ├── __init__.py          # Module exports
│   ├── excel_parser.py      # Excel parsing
│   ├── docx_handler.py      # Word document handling
│   ├── change_detector.py   # Change detection
│   ├── llm_caller.py        # Claude API integration
│   └── approval_workflow.py # Approval management
│
├── utils/                    # Utility modules
│   ├── __init__.py
│   ├── validators.py        # Input validation
│   ├── logger.py            # Logging setup
│   ├── cache_manager.py     # Response caching
│   └── file_storage.py      # JSON file operations
│
├── data/                     # Data storage (created at runtime)
│   ├── changes/             # Individual change JSON files
│   ├── metadata/            # Metadata and logs
│   ├── cache/               # LLM response cache
│   ├── uploads/             # Uploaded Excel files
│   └── master_policy.docx   # Master document
│
└── logs/                     # Application logs
    └── app.log              # Main application log
```

---

## Troubleshooting

### Issue: "ANTHROPIC_API_KEY not set"

**Solution:**
```bash
# Check if .env exists
ls -la .env

# If not, create it
cp .env.example .env

# Edit .env and add your API key
ANTHROPIC_API_KEY=your-actual-key-here

# Verify it's set
grep ANTHROPIC_API_KEY .env
```

### Issue: "Backend not found on port 8000"

**Solution:**
```bash
# Start backend first
./run_backend.sh

# Wait 2-3 seconds for it to start

# In another terminal, start frontend
./run_frontend.sh

# Or check if another process is using port 8000
lsof -i :8000
```

### Issue: "Cannot connect to API. Make sure FastAPI server is running"

**Solution:**
1. Verify backend is running: `curl http://localhost:8000/api/health`
2. Check firewall allows port 8000
3. Restart backend: `./run_backend.sh`

### Issue: "Module not found" errors

**Solution:**
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install --upgrade --force-reinstall -r requirements.txt

# Clear Python cache
find . -type d -name __pycache__ -exec rm -r {} +
find . -type f -name "*.pyc" -delete
```

### Issue: "Permission denied" on shell scripts

**Solution:**
```bash
# Make scripts executable
chmod +x run_backend.sh run_frontend.sh run_all.sh

# Run again
./run_all.sh
```

### Issue: Port already in use

**Solution:**
```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use different ports in .env
API_PORT=8001
STREAMLIT_PORT=8502
```

### View Logs for Debugging

```bash
# Watch logs in real-time
tail -f logs/app.log

# Search for errors
grep ERROR logs/app.log

# Get last 50 lines
tail -50 logs/app.log
```

---

## Docker Setup (Optional)

### Build Docker Image

```bash
# Create Dockerfile
cat > Dockerfile << 'EOF'
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000 8501

CMD ["./run_all.sh"]
EOF

# Build image
docker build -t creditpolicyiq .
```

### Run with Docker

```bash
# Set API key
export ANTHROPIC_API_KEY="your-key"

# Run container
docker run -p 8000:8000 -p 8501:8501 \
  -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
  -v $(pwd)/data:/app/data \
  creditpolicyiq
```

---

## Performance Tuning

### For Large Files
```bash
# Increase available memory
# Linux: check with `free -h`
# Ensure 4GB+ free RAM

# Increase LLM timeout
LLM_TIMEOUT=30  # seconds

# Reduce concurrent requests
# In app.py modify worker count
```

### For Production
```bash
# Use production ASGI server
pip install gunicorn

# Start with Gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

---

## Next Steps

1. **Verify Installation**
   ```bash
   ./run_all.sh
   ```

2. **Upload Sample Excel**
   - Navigate to http://localhost:8501
   - Go to "📤 Upload Excel"
   - Upload sample policy changes

3. **Review Changes**
   - Go to "🔍 Review Changes"
   - Translate changes with Claude

4. **Approve Changes**
   - Go to "✅ Approve Changes"
   - Review and approve recommended changes

5. **Apply to Master**
   - Go to "📄 Master Document"
   - Apply all approved changes
   - Download updated document

---

## Support & Documentation

- **Project Plan**: See `VALIDATION.md` for architecture details
- **README**: See `README.md` for comprehensive documentation
- **API Docs**: Visit http://localhost:8000/docs for interactive API reference

---

## Cleanup

To remove and restart:

```bash
# Deactivate virtual environment
deactivate

# Remove virtual environment
rm -rf venv

# Remove cache
rm -rf __pycache__ .pytest_cache

# Start fresh
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run
./run_all.sh
```

---

**Last Updated**: 2024-04-06  
**Status**: ✅ Ready for Deployment
