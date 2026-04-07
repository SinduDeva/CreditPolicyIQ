# Master Document Upload Guide

This guide explains how to upload and manage the master credit policy document.

---

## 📤 **Uploading Master Document**

### **Via Streamlit Dashboard (Recommended)**

1. **Navigate to Master Document page**
   - Click "📄 Master Document" in sidebar
   - Go to "📤 Upload Master" tab

2. **Choose file**
   - Click "Choose master document"
   - Select your .docx file
   - Must be .docx format (Word document)

3. **Confirm upload**
   - Review file information
   - Check the confirmation checkbox
   - Click "📤 Upload Master Document"

4. **Verify success**
   - See confirmation message
   - Previous version is auto-backed up
   - Can now review and apply changes

### **Via API Endpoint**

```bash
# Upload master document
curl -X POST http://localhost:8000/api/upload-master \
  -F "file=@/path/to/master_policy.docx"

# Response:
{
  "status": "success",
  "filename": "master_policy.docx",
  "size": 45234,
  "message": "Master document updated successfully",
  "backup_path": "data/backups/master_policy_backup_20240406_143022.docx"
}
```

### **Python SDK**

```python
import requests

files = {'file': open('master_policy.docx', 'rb')}
response = requests.post(
    'http://localhost:8000/api/upload-master',
    files=files
)

print(response.json())
```

---

## 🔄 **Master Document Workflow**

```
Step 1: Upload Master Document
        │
        ├─ File validated (.docx format)
        ├─ Previous version backed up
        ├─ Document structure extracted
        └─ Ready for changes

Step 2: Upload Excel with Changes
        │
        ├─ Changes detected
        ├─ Matched to master sections
        └─ Awaiting review

Step 3: Review & Translate
        │
        ├─ Review suggested changes
        ├─ LLM translates to Word format
        └─ Awaiting approval

Step 4: Approve Changes
        │
        ├─ Approve with comments
        ├─ Or reject with reasons
        └─ Ready to apply

Step 5: Apply Changes
        │
        ├─ New version created
        ├─ Changes applied with formatting
        └─ Version tracked
```

---

## 📋 **Master Document Requirements**

### **File Format**
- ✅ Must be `.docx` (Microsoft Word format)
- ✅ Maximum 50 MB
- ❌ Not supported: `.doc`, `.pdf`, `.txt`, `.odt`

### **Document Structure**
Good to have for better change matching:
- ✅ Clear section headings
- ✅ Logical organization
- ✅ Consistent formatting
- ✅ Section numbering (e.g., 1, 1.1, 1.1.1)

### **Example Structure**
```
Credit Policy - Master Document

1. Overview
   1.1 Purpose
   1.2 Applicability

2. Eligibility Criteria
   2.1 Credit Score
   2.2 Income Requirements
   2.3 Age Restrictions

3. Loan Products
   3.1 Personal Loans
   3.2 Home Loans
   3.3 Business Loans

4. Documentation Requirements
```

---

## 🔐 **Auto-Backup Feature**

Every time you upload a new master document:

1. **Previous version backed up**
   ```
   data/backups/
   ├── master_policy_backup_20240406_143022.docx
   ├── master_policy_backup_20240406_120015.docx
   └── master_policy_backup_20240406_090030.docx
   ```

2. **Backup location in response**
   ```json
   {
     "backup_path": "data/backups/master_policy_backup_20240406_143022.docx"
   }
   ```

3. **Manual recovery**
   ```bash
   cp data/backups/master_policy_backup_20240406_143022.docx \
      data/master_policy.docx
   ```

---

## 🎯 **Initial Setup**

### **First Time Usage**

```bash
# 1. Start application
./run_all.sh

# 2. Open dashboard
# http://localhost:8501

# 3. Navigate to Master Document page
# Click "📄 Master Document" in sidebar

# 4. Click "📤 Upload Master" tab

# 5. Upload your credit policy document
# Select .docx file → Upload

# 6. Confirm upload successful
# Now ready to process Excel changes!
```

### **Testing Without Master Document**

If you don't have a master document yet:

```bash
# 1. Create a simple test document
# - Open Microsoft Word or LibreOffice
# - Create basic sections
# - Save as .docx

# 2. Or download a sample
# Check docs/ folder for examples

# 3. Upload via dashboard
```

---

## ✨ **Features with Master Document**

### **Enabled After Upload**

✅ **Change Detection**
- Match Excel changes to document sections
- Calculate confidence scores
- Identify affected areas

✅ **Context Awareness**
- Understand surrounding text
- Preserve formatting
- Suggest better placements

✅ **Smart Formatting**
- Recommend paragraph vs bullet vs table
- Match document style
- Maintain consistency

✅ **Version Control**
- Track all changes
- Create versions on apply
- Backup on upload

---

## 🔧 **Troubleshooting**

### **Error: "File must be .docx format"**

**Solution:**
- Ensure file is in .docx format
- Not .doc, .pdf, or other formats
- Save as "Word Document (.docx)"

### **Error: "File size exceeds limit"**

**Solution:**
- Check file size: Must be < 50 MB
- Compress images in document
- Reduce document complexity

### **Error: "Could not validate document"**

**Solution:**
- Document still uploaded (backup created)
- But might have structural issues
- Try opening/saving in Word first
- Remove any corrupted objects

### **Upload appears stuck**

**Solution:**
- Check file size (large files take time)
- Ensure stable internet connection
- Try uploading again
- Check logs: `tail -f logs/app.log`

---

## 📊 **Monitoring Master Documents**

### **View Upload History**

```bash
# Check master upload log
cat data/metadata/master_upload_log.json

# Example:
{
  "entries": [
    {
      "timestamp": "2024-04-06T14:30:22.123456",
      "filename": "master_policy.docx",
      "size": 45234,
      "action": "master_document_uploaded"
    }
  ]
}
```

### **Check Backups**

```bash
# List all backups
ls -lh data/backups/

# Restore if needed
cp data/backups/master_policy_backup_<timestamp>.docx \
   data/master_policy.docx
```

### **Verify Document Structure**

```bash
# Check via API
curl http://localhost:8000/api/master/versions | jq

# Or check in dashboard
# Master Document → 📥 Download & Info tab
```

---

## 🔄 **Workflow Examples**

### **Scenario 1: Initial Setup**

```
Day 1:
  1. Create credit policy in Word
  2. Save as master_policy.docx
  3. Open CreditPolicyIQ dashboard
  4. Upload master via "📤 Upload Master"
  5. Ready to process changes!
```

### **Scenario 2: Policy Update**

```
Day 1:
  1. Receive new Excel with policy changes
  2. Upload Excel via "📤 Upload Excel"
  3. Review suggested changes
  4. Approve changes

Day 2:
  1. Go to "Master Document" page
  2. Apply approved changes
  3. Download updated document
  4. Send to stakeholders

Later:
  1. Get feedback from stakeholders
  2. Make adjustments
  3. Upload new master if major revision
  4. Or upload new Excel for incremental changes
```

### **Scenario 3: Multiple Versions**

```
Version 1.0:
  - Upload initial master
  - Apply changes
  - Create version 1.0

Version 1.1:
  - Upload Excel with updates
  - Apply to version 1.0
  - Create version 1.1

Version 2.0:
  - Major rewrite
  - Upload new master document
  - Create version 2.0 from scratch
```

---

## 📚 **Best Practices**

### **Document Organization**
- ✅ Use clear section numbers
- ✅ Consistent heading styles
- ✅ Logical structure
- ✅ Meaningful section titles

### **Change Management**
- ✅ One change per row in Excel
- ✅ Clear section references
- ✅ Descriptive change notes
- ✅ Use color highlighting (GREEN/YELLOW/RED)

### **Backup Strategy**
- ✅ System auto-backs up on upload
- ✅ Keep copies of important versions
- ✅ Test in staging first
- ✅ Get approval before applying

### **Documentation**
- ✅ Note which Excel corresponds to master version
- ✅ Keep change logs
- ✅ Document approval chain
- ✅ Track stakeholder feedback

---

## 🚀 **Tips & Tricks**

### **Faster Matching**
- Use consistent section naming
- Match Excel section names to master
- Add section IDs for clarity

### **Better Suggestions**
- Provide good context in Excel
- Include technical details
- Add notes explaining changes

### **Batch Updates**
- Group related changes in one Excel
- Upload one master document
- Review all changes together
- Apply as single batch

### **Testing**
- Use mock provider first (no API key)
- Test with sample documents
- Verify formatting after apply
- Keep backups!

---

## 🎓 **Advanced Usage**

### **API Integration**

```python
import requests

# Upload master
files = {'file': open('policy.docx', 'rb')}
r = requests.post('http://localhost:8000/api/upload-master', files=files)

# Get current master versions
versions = requests.get('http://localhost:8000/api/master/versions').json()

# Check pending changes
pending = requests.get('http://localhost:8000/api/changes/pending').json()

# Apply all approved
result = requests.post('http://localhost:8000/api/master/apply-changes').json()
```

### **Automation**

```bash
#!/bin/bash
# Auto-upload and process changes

MASTER_FILE="master_policy.docx"
EXCEL_FILE="changes_$(date +%Y%m%d).xlsx"

# Upload master
curl -X POST http://localhost:8000/api/upload-master \
  -F "file=@$MASTER_FILE"

# Upload changes
curl -X POST http://localhost:8000/api/upload-excel \
  -F "file=@$EXCEL_FILE"

# Apply changes
curl -X POST http://localhost:8000/api/master/apply-changes
```

---

## ✅ **Summary**

| Task | Method | Time |
|------|--------|------|
| Upload master | Dashboard or API | 1 min |
| Download version | API endpoint | <1 min |
| View backups | File system | <1 min |
| Restore backup | Copy file | <1 min |

**Master document upload is essential for using CreditPolicyIQ!**

Start by uploading your initial credit policy document, then you can begin processing policy changes from Excel files.

---

**See also:**
- [SETUP.md](SETUP.md) - Initial setup
- [LLM_PROVIDERS.md](LLM_PROVIDERS.md) - LLM configuration
- [README.md](README.md) - Full documentation
