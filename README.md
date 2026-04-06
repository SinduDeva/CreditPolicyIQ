# CreditPolicyIQ - Credit Policy Automation POC

A comprehensive solution for automating credit policy changes using AI-powered analysis and human-in-the-loop approval workflows.

## Features

### Core Modules
- **Excel Parser**: Parse policy changes from Excel with color-coded detection (NEW/MODIFIED/DELETED)
- **DOCX Handler**: Extract and manipulate Word document structure
- **Change Detector**: Fuzzy-match Excel changes to master document sections
- **LLM Caller**: Claude API integration for intelligent policy translation
- **Approval Workflow**: Manage change approval lifecycle with versioning

### FastAPI Backend
- RESTful API for file management, change tracking, and approvals
- JSON file-based storage
- Comprehensive logging
- CORS support for frontend integration

### Streamlit Dashboard
- Interactive 7-page interface
- Real-time change monitoring
- LLM-powered suggestions
- Approval workflows with confirmation dialogs
- Version history tracking
- Activity logs

## Installation

### Prerequisites
- Python 3.9+
- Anthropic API key (for Claude integration)

### Setup

1. **Clone repository and navigate to project:**
```bash
cd /home/user/CreditPolicyIQ
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Configure API Key:**
```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

4. **Create required data directories:**
```bash
mkdir -p data/changes data/metadata data/cache data/uploads logs
```

## Running the Application

### Start FastAPI Backend
```bash
python app.py
```
The API will be available at `http://localhost:8000`
- Interactive docs: `http://localhost:8000/docs`
- OpenAPI schema: `http://localhost:8000/openapi.json`

### Start Streamlit Dashboard (in another terminal)
```bash
streamlit run streamlit_app.py
```
The dashboard will be available at `http://localhost:8501`

## Project Structure

```
CreditPolicyIQ/
├── app.py                      # FastAPI main application
├── streamlit_app.py            # Streamlit dashboard
├── config.py                   # Configuration management
├── core/                       # Core business logic modules
│   ├── excel_parser.py         # Excel file parsing
│   ├── docx_handler.py         # Word document handling
│   ├── change_detector.py      # Change detection & matching
│   ├── llm_caller.py           # Claude API integration
│   └── approval_workflow.py    # Approval workflow management
├── utils/                      # Utility modules
│   ├── validators.py           # Input validation
│   ├── logger.py               # Logging configuration
│   ├── cache_manager.py        # Response caching
│   └── file_storage.py         # JSON file operations
├── data/                       # Data storage (created at runtime)
│   ├── changes/                # Individual change JSON files
│   ├── metadata/               # Metadata and logs
│   ├── cache/                  # LLM response cache
│   └── uploads/                # Uploaded files
└── logs/                       # Application logs
```

## API Endpoints

### Upload & File Management
- `POST /api/upload-excel` - Upload and parse Excel file
- `GET /api/master/current` - Download current master document
- `GET /api/master/versions` - List all document versions

### Change Management
- `GET /api/changes/pending` - Get pending changes
- `POST /api/changes/{change_id}/translate` - Translate change with Claude
- `POST /api/changes/{change_id}/approve` - Approve a change
- `POST /api/changes/{change_id}/reject` - Reject a change

### Apply Changes
- `POST /api/master/apply-changes` - Apply all approved changes

### Logs
- `GET /api/logs/changes` - View changes log
- `GET /api/logs/approvals` - View approvals log

## Streamlit Pages

### 1. Dashboard
- Metrics: Pending, Total, Approved changes; Document count
- Recent changes table
- Auto-refresh on load

### 2. Upload Excel
- .xlsx file uploader
- Required columns validation
- Change detection and summary
- Detected changes table

### 3. Review Changes
- View pending changes with expandable cards
- Translate button for pending changes
- View LLM suggestions with confidence scores
- Master document context matching

### 4. Approve Changes
- Expandable cards for changes ready for approval
- Side-by-side approve/reject buttons
- Comment/reason input fields
- Confirmation dialogs

### 5. Master Document
- Download current master document
- Apply approved changes button with confirmation
- Version and changes applied metrics

### 6. Version History
- Table of all document versions
- Version metadata (created date, changes applied)
- Total version count

### 7. Logs
- Two-column layout with changes and approvals logs
- Filterable tables
- Timestamp tracking

## Configuration

### Environment Variables
- `ANTHROPIC_API_KEY` - Anthropic API key for Claude
- `MASTER_DOCX_PATH` - Path to master DOCX file (default: data/master_policy.docx)
- `EXCEL_PATH` - Path to Excel file (default: data/policy_changes.xlsx)

### Config File
Edit `config.py` to customize:
- API key location
- File paths
- Max tokens for LLM
- Model selection

## Workflow

1. **Upload Excel**: Administrator uploads policy changes in Excel format
2. **Detect Changes**: System automatically detects changes and matches to master document
3. **Review**: Analyst reviews changes and translates with Claude if needed
4. **Approve/Reject**: Changes are approved with comments or rejected with reasons
5. **Apply**: Apply all approved changes to create new master document version
6. **Track**: All actions logged for audit trail

## Color-Coded Changes

In Excel files:
- 🟢 **Green (FF00B050)** - NEW policy
- 🟡 **Yellow (FFFFFF00)** - MODIFIED policy
- 🔴 **Red (FFFF0000)** - DELETED policy

## Error Handling

- All API endpoints return proper HTTP status codes
- File operations include size validation
- API calls include connection error handling
- Logging captures all operations for debugging

## Development

### Running Tests
```bash
pytest tests/
```

### Code Quality
```bash
pylint *.py core/ utils/
```

## License

POC - Internal Use Only

## Support

For issues or questions, contact the development team.
