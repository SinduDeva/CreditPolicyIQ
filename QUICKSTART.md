# CreditPolicyIQ - Quick Start Guide

**Complete setup in 5 minutes. No fluff, no repeating steps.**

---

## ⚡ **5-Minute Quick Start**

### Step 1: Clone & Navigate
```bash
cd /home/user/CreditPolicyIQ
```

### Step 2: Configure (Optional)
```bash
cp .env.example .env
# ✅ App works with default settings (mock provider, no API key needed)
# Optional: Add your LLM API key to enable AI features
#   LLM_API_KEY=your-api-key-here
#   LLM_PROVIDER=anthropic (or openai)
```

### Step 3: Start with One Command
```bash
./run_all.sh
```

**What run_all.sh does automatically:**
1. ✅ Detects Python (python3 or python)
2. ✅ Creates virtual environment (venv/)
3. ✅ **Installs all dependencies** from requirements.txt
   - fastapi, uvicorn, pydantic, streamlit
   - pandas, openpyxl for Excel/document processing
   - anthropic, requests for API calls
   - No build tools or compilation needed
4. ✅ Creates .env file if missing
5. ✅ Starts FastAPI backend (port 8000)
6. ✅ Starts Streamlit dashboard (port 8501)

**Installation time:** ~2 minutes (first run) | ~10 seconds (subsequent runs)

### Step 4: Open Dashboard
- **Dashboard**: http://localhost:8501
- **API Docs**: http://localhost:8000/docs

✅ **Done!** Application is ready to use.

---

## 📋 **Requirements & Compatibility**

### System Requirements
- **Python:** 3.9 or higher (tested: 3.13 on Windows)
- **OS:** Windows, macOS, or Linux
- **RAM:** 4GB minimum
- **Storage:** ~500MB for installation + data

### Cross-Platform Validation
✅ **All packages are cross-platform compatible:**
- Windows (32/64-bit)
- macOS (Intel & Apple Silicon)
- Linux (AMD64 & ARM64)

See `REQUIREMENTS_VALIDATION.md` for detailed compatibility report.

### What Gets Installed
```
Core Framework:
  ✅ fastapi (0.109.0+)      - REST API framework
  ✅ uvicorn (0.27.0+)       - ASGI server
  ✅ streamlit (1.28.0+)     - Dashboard UI

Data Processing:
  ✅ pandas (2.0.0+)         - Data analysis
  ✅ openpyxl (3.0.0+)       - Excel parsing
  ✅ python-docx (0.8.11+)   - Word documents

Web & Validation:
  ✅ pydantic (2.6.0+)       - Data validation
  ✅ requests (2.31.0+)      - HTTP client
  ✅ python-multipart        - Form processing

LLM (Optional):
  ✅ anthropic (0.7.0+)      - Claude API
  ⚪ openai (optional)       - OpenAI API

Total Size: ~300-400MB (includes dependencies)
```

---

## 🎯 **Complete Workflow**

### 1️⃣ **Upload Master Document**
- Dashboard → "📄 Master Document" → "📤 Upload Master"
- Choose your `.docx` credit policy file
- Confirm upload
- System auto-backs up previous version

**API:** `POST /api/upload-master`

### 2️⃣ **Upload Excel with Changes**
- Dashboard → "📤 Upload Excel"
- Choose `.xlsx` file with policy changes
- Color-code changes:
  - 🟢 GREEN = NEW
  - 🟡 YELLOW = MODIFIED
  - 🔴 RED = DELETED
- Upload

**Excel columns:**
```
REQUIRED (minimum):
- Section_Name .......................... Name of the policy section
- Policy_Content ........................ The policy text/content

OPTIONAL (for enhanced features):
- Section_ID ............................ Unique identifier (auto-generated if missing)
- UW_Technical_Details .................. Technical underwriting notes
- Status ............................... Change status (defaults to PENDING)
- Color_Flag ............................ Cell background color for change type
  * GREEN (#00B050) = NEW
  * YELLOW (#FFFF00) = MODIFIED
  * RED (#FF0000) = DELETED
- Notes ................................ Additional notes
```

**API:** `POST /api/upload-excel`

### 3️⃣ **Review Changes**
- Dashboard → "🔍 Review Changes"
- See Excel content vs Master context
- Click "🤖 Translate with Claude" for AI suggestions
- Or use mock provider (no API key needed)

**API:** `GET /api/changes/pending` + `POST /api/changes/{id}/translate`

### 4️⃣ **Approve/Reject**
- Dashboard → "✅ Approve Changes"
- Review each suggested change
- Approve with optional comment
- Or reject with reason
- All logged for audit

**API:** `POST /api/changes/{id}/approve` or `POST /api/changes/{id}/reject`

### 5️⃣ **Apply Changes**
- Dashboard → "📄 Master Document" → "🚀 Apply Changes"
- View approved changes
- Click "Apply All Approved Changes"
- Confirm
- New version created, previous auto-backed up

**API:** `POST /api/master/apply-changes`

### 6️⃣ **Download Updated Document**
- Dashboard → "📄 Master Document" → "📥 Download & Info"
- Or: `GET /api/master/current`

**Result:** Updated master document with all approved changes ✅

---

## 📋 **Configuration**

### Default Settings ✅
**Out of the box, the app works with no setup needed:**
- **LLM Provider:** mock (no API key required)
- **Dashboard:** http://localhost:8501
- **API:** http://localhost:8000

### Optional: Enable AI Features
To use Anthropic Claude or OpenAI models, update `.env`:

```bash
# === LLM PROVIDER (Optional) ===
LLM_PROVIDER=anthropic          # anthropic, openai, or mock (default)
LLM_API_KEY=sk-ant-xxx...       # Your API key here
LLM_MODEL=claude-3-5-sonnet-20241022  # Auto-selects if not set
```

### LLM Provider Options

| Provider | Cost | API Key | Quality | Default |
|----------|------|---------|---------|---------|
| **mock** | FREE | ❌ No | Basic | ✅ Yes |
| **anthropic** | Low | ✅ Yes | Best | Optional |
| **openai** | Higher | ✅ Yes | Good | Optional |

**Works without any API key!** Default mock provider is perfect for testing. ✅

---

## 📂 **File Structure**

```
CreditPolicyIQ/
├── app.py ........................ FastAPI backend
├── streamlit_app.py .............. Streamlit dashboard
├── .env.example .................. Configuration template
├── requirements.txt .............. Dependencies
│
├── core/ ......................... Business logic
│   ├── excel_parser.py ......... Parse Excel files
│   ├── docx_handler.py ......... Handle Word documents
│   ├── change_detector.py ...... Find changes
│   ├── llm_caller.py ........... LLM integration
│   ├── llm_provider.py ......... LLM providers (Anthropic/OpenAI/Mock)
│   └── approval_workflow.py .... Approval system
│
├── utils/ ........................ Utilities
│   ├── validators.py ........... Validation
│   ├── logger.py ............... Logging
│   ├── cache_manager.py ........ Caching
│   └── file_storage.py ......... JSON storage
│
├── data/ ......................... Runtime data
│   ├── master_policy.docx ...... Current master document
│   ├── changes/ ................ Change files (JSON)
│   ├── metadata/ ............... Logs
│   ├── backups/ ................ Master backups
│   └── cache/ .................. LLM response cache
│
└── logs/ ......................... Application logs
```

---

## 🔧 **Installation & Troubleshooting**

### Installation Failed?

#### "Python not found"
```bash
# Verify Python is installed
python --version  # or python3 --version

# If not installed:
# Windows: Download from https://python.org
# macOS: brew install python3
# Linux: sudo apt-get install python3
```

#### "Dependencies installation failed"
```bash
# Clean up and retry
rm -rf venv
./run_all.sh

# If still failing, check:
# - Internet connection (pip needs to download packages)
# - Disk space (500MB free recommended)
# - Python version (3.9+ required)
```

#### "Pydantic/pandas compilation error"
✅ **Already fixed!** The requirements.txt uses flexible versions that:
- Skip Rust compilation (pydantic>=2.6.0 has pre-built wheels)
- Skip C compilation (pandas>=2.0.0 works on Python 3.13)
- Use universal wheels (cross-platform)

If you still see compiler errors, ensure you have the latest requirements.txt

#### "Can't find venv or pip"
```bash
# On Windows, try explicit paths
C:\Users\YourName\AppData\Local\Programs\Python\Python313\python.exe -m venv venv

# On macOS/Linux
/usr/bin/python3 -m venv venv
```

### Runtime Issues

#### "Backend not found on port 8000"
```bash
# Check if backend is running
ps aux | grep "python.*app.py"

# Or manually start in terminal 1
source venv/bin/activate
python app.py
```

#### "Cannot connect to API"
```bash
# Verify backend is responding
curl http://localhost:8000/api/health

# Result should be: {"status": "healthy"}
```

#### "Cannot translate changes with mock provider"
✅ **Mock provider generates sample suggestions.** To get AI-powered suggestions:
- **Option 1:** Go to ⚙️ Settings → 🔑 API Keys to add Anthropic/OpenAI key
- **Option 2:** Edit `.env` with your API key and restart app
- **For now:** Mock provider works perfectly for testing! ✅

#### "Excel upload fails"
- Ensure file is `.xlsx` (not `.xls` or `.csv`)
- Check required columns exist
- File size < 500 MB (configurable)

#### "Cannot update master document"
- Ensure `.docx` format (not `.doc`)
- File size < 500 MB (configurable)
- Previous version is auto-backed up

---

## 📊 **API Reference**

### Upload Endpoints
```bash
# Upload Master Document
POST /api/upload-master
Content-Type: multipart/form-data
file: <.docx file>

# Upload Excel Changes
POST /api/upload-excel
Content-Type: multipart/form-data
file: <.xlsx file>
```

### Download Endpoint
```bash
# Download Current Master Document
GET /api/master/current
# Returns: .docx file
```

### View & Manage
```bash
# Get pending changes
GET /api/changes/pending

# Translate change
POST /api/changes/{change_id}/translate

# Approve change
POST /api/changes/{change_id}/approve
Body: {"user": "name", "comment": "optional"}

# Reject change
POST /api/changes/{change_id}/reject
Body: {"reason": "reason text"}

# Apply all approved
POST /api/master/apply-changes

# Get versions
GET /api/master/versions

# Get logs
GET /api/logs/changes
GET /api/logs/approvals
```

### Full API Docs
Visit: http://localhost:8000/docs

---

## ✨ **Key Features**

| Feature | Access |
|---------|--------|
| **Upload Master Doc** | Dashboard or API |
| **Upload Excel Changes** | Dashboard or API |
| **Auto-Backup** | Automatic on every master upload |
| **Change Detection** | Automatic with color detection |
| **LLM Translation** | Dashboard or API (optional with mock) |
| **Review & Approve** | Dashboard UI |
| **Download Document** | Dashboard or API |
| **Version History** | Dashboard page |
| **Audit Logs** | Dashboard page |
| **Backup Recovery** | `data/backups/` folder |

---

## 🚀 **LLM Configuration** (All Optional)

### 1️⃣ Current Status
- **Default Provider:** mock (no API key needed)
- **AI Features:** Available with mock suggestions
- **No Cost:** Use as-is with no additional setup

### 2️⃣ Upgrade to Anthropic Claude (Recommended)
1. Visit https://console.anthropic.com/keys
2. Create new API key
3. Edit `.env` and update:
   ```
   LLM_PROVIDER=anthropic
   LLM_API_KEY=sk-ant-xxx...
   ```
4. Restart application
5. Dashboard now uses Claude for better suggestions ✨

### 3️⃣ Or Use OpenAI GPT
1. Visit https://platform.openai.com/api-keys
2. Create API key
3. Edit `.env`:
   ```
   LLM_PROVIDER=openai
   LLM_API_KEY=sk-xxx...
   LLM_MODEL=gpt-4-turbo
   ```
4. Restart application

### 4️⃣ Manage API Keys in Dashboard
- Go to **⚙️ Settings** → **🔑 API Keys**
- View current provider and API key status
- Get instructions for updating keys
- No restart needed from settings page (manual .env edit required)

---

## 📚 **Additional Documentation**

| Document | Purpose |
|----------|---------|
| **README.md** | Full feature overview |
| **FEATURE_VALIDATION.md** | Feature checklist |
| **MASTER_DOCUMENT_GUIDE.md** | Master doc management |
| **LLM_PROVIDERS.md** | LLM configuration details |
| **DEPLOYMENT_READY.md** | Production readiness checklist |

---

## ✅ **What You Can Do Now**

✅ Upload master credit policy document  
✅ Upload Excel with policy changes  
✅ Auto-detect changes with color highlighting  
✅ Review changes with AI suggestions (or mock)  
✅ Approve/reject with audit trail  
✅ Apply to master document safely  
✅ Download updated document  
✅ View version history  
✅ Access complete audit logs  
✅ Works with or without API key  

---

## 🎓 **Example Workflow**

```bash
# Terminal 1: Start app
./run_all.sh
# App running at:
# - Dashboard: http://localhost:8501
# - API: http://localhost:8000/docs

# Browser: Open http://localhost:8501
# 1. Master Document → Upload your policy.docx
# 2. Upload Excel → Upload your changes.xlsx
# 3. Review Changes → See suggestions (with AI or mock)
# 4. Approve Changes → Approve each change
# 5. Master Document → Apply all approved
# 6. Download updated master_policy.docx ✅
```

---

**That's it! Questions?** Check the full docs or use the API docs at http://localhost:8000/docs
