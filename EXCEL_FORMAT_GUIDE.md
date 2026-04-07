# Excel Format Guide - CreditPolicyIQ

**No predefined format required!** The tool intelligently detects changes based on cell highlighting color.

---

## 📋 **How It Works**

The Excel parser scans **all sheets** in your workbook and identifies changes by **color highlighting**, not by specific columns or structure.

### Change Detection by Color

| Color | Meaning | Action |
|-------|---------|--------|
| 🟢 **GREEN** | New Content | Add to master document |
| 🟡 **YELLOW** | Modified Content | Update in master document |
| 🔴 **RED** | Deleted Content | Remove from master document |

---

## ✅ **What You Can Do**

### ✅ Any Excel Structure Works

You don't need specific columns or format. Just highlight the cells you want to change!

**Example 1: Simple Table**
```
| Section | Current Policy | New Policy |
|---------|----------------|------------|
| Coverage| $500K limit    | $1M limit  | ← Highlight in YELLOW
|         |                | Add dental | ← Highlight in GREEN
```

**Example 2: Mixed Structure**
```
Coverage Details:
- Current deductible: $500 ← This text in YELLOW (to be modified)
- New coverage: Add life insurance ← Highlight in GREEN
- Remove: Legacy plan text ← Highlight in RED
```

**Example 3: Multiple Sheets**
```
Sheet 1: "Medical Policy"
  - New coverage: Add vision (YELLOW)
  
Sheet 2: "Dental Policy"  
  - Increase limit to $2000 (GREEN)
  - Remove: Prior authorization (RED)
```

### ✅ Flexible Content

The tool extracts:
- **The highlighted text itself** - treated as the change content
- **Surrounding context** - used to understand the change
- **Sheet name & location** - tracked for reference

### ✅ Multiple Sheets

All sheets in the workbook are scanned. The tool:
- Processes all sheets automatically
- Preserves sheet names in change metadata
- Combines all changes into one update list

---

## 📝 **Best Practices**

### 1. **Highlight Only the Change**
```
✅ GOOD: Just the text that's new/modified
- CURRENT: "Coverage limit is $500K"
- ADD IN GREEN: "$1M"
- RESULT: "Coverage limit is $1M"

❌ AVOID: Highlighting entire paragraphs
```

### 2. **Provide Context**
```
✅ GOOD: Cell has surrounding text for context
  | Policy Section | Current | Updated |
  | Coverage Limit | $500K   | $1M |   ← Clear what changed

❌ AVOID: Isolated colored cells with no context
```

### 3. **Use One Color Per Change**
```
✅ GOOD: Each change in one color
- Line 1: GREEN "Add vision coverage"
- Line 2: YELLOW "Change deductible to $250"
- Line 3: RED "Remove legacy plan"

❌ AVOID: Mixing colors in same cell or change
```

### 4. **Clear Descriptions**
```
✅ GOOD: Specific, actionable text
- "Increase annual maximum to $50,000"
- "Add prescription drug coverage"
- "Remove out-of-network limit"

❌ AVOID: Vague text
- "Change something"
- "Update policy"
```

---

## 🎯 **Examples**

### Example 1: Medical Policy Updates

**Excel File: `medical_policy_changes.xlsx`**

**Sheet: "Coverage Changes"**
```
Medical Policy Update - April 2026

Coverage Summary:
- Basic coverage: Unchanged
- Enhanced coverage: Remove annual deductible (RED)
- Premium coverage: Add dental services (GREEN)
  - Preventive: 100% coverage
  - Basic: 80% coverage
  - Modify copay for specialist: $50 to $75 (YELLOW)

Effective Date: April 1, 2026
```

**What the tool finds:**
1. ✅ RED highlighted text: "Remove annual deductible"
2. ✅ GREEN highlighted text: "Add dental services"
3. ✅ YELLOW highlighted text: "$75"

**Auto-generated for each:**
- Change ID: Unique identifier
- Type: NEW, MODIFIED, or DELETED
- Content: The highlighted text
- Context: Surrounding text for understanding
- Source: Sheet name and cell location

---

### Example 2: Multi-Sheet Policy Update

**File: `policy_comprehensive_update.xlsx`**

**Sheet 1: "Medical"**
```
Maximum Out-of-Pocket: Increase to $3,000 (YELLOW)
New: Mental health parity - 1:1 coverage (GREEN)
```

**Sheet 2: "Dental"**
```
Remove: Waiting periods (RED)
Increase coverage: Orthodontics to 50% (YELLOW)
```

**Sheet 3: "Vision"**
```
New benefit: Frames every 24 months (GREEN)
```

**Tool processes all 3 sheets and creates changes:**
- 1 YELLOW change (Medical)
- 1 GREEN + 1 RED + 1 YELLOW (Dental)
- 1 GREEN (Vision)
- **Total: 5 changes detected**

---

### Example 3: Simple Two-Column Format

**File: `simple_changes.xlsx`**

```
| Current Policy | New Policy |
|----------------|-----------|
| Deductible: $500 | Deductible: $250 (YELLOW - in New Policy column) |
| | Add vision coverage (GREEN - in New Policy column) |
| Out-of-network applies | (RED - remove this line) |
```

---

## 🔄 **How Changes Are Applied**

After you upload the Excel file:

1. **Detection** → Tool finds all colored cells in all sheets
2. **Extraction** → Pulls text and context from each colored cell
3. **Matching** → Finds where to apply each change in master document
4. **Review** → Shows you all detected changes for approval
5. **Edit** → You can refine the suggested wording
6. **Approve** → Mark as approved for application
7. **Apply** → Updates are merged into master document

---

## ⚠️ **Important Notes**

### Color Specifications

Use standard Excel colors for best results:

- **GREEN**: RGB (0, 176, 80) or close variations
- **YELLOW**: RGB (255, 255, 0) or close variations  
- **RED**: RGB (255, 0, 0) or close variations

### Supported Formats

- ✅ `.xlsx` (Excel 2007+) - Recommended
- ✅ `.xls` (Excel 97-2003) - Supported
- ❌ `.csv` (no color support)
- ❌ `.ods` (OpenDocument - limited support)

### Size Limits

- Maximum file size: **500 MB** (configurable)
- Maximum sheets: Unlimited
- Maximum changes per file: Unlimited

### Cell Content

- Text: ✅ Full support
- Numbers: ✅ Treated as text
- Formulas: ❌ Values only (not formulas)
- Images: ❌ Not extracted

---

## 🔍 **Troubleshooting**

### "No changes detected"
- ✅ Make sure cells are actually highlighted (not just border)
- ✅ Use proper colors: GREEN, YELLOW, or RED
- ✅ Check that all sheets contain at least one colored cell

### "Wrong number of changes"
- ✅ Each colored cell is one change
- ✅ Adjacent colored cells are separate changes
- ✅ Same color in different sheets = separate changes

### "Context not extracted properly"
- ✅ Make sure neighboring cells have relevant text
- ✅ Provide context above/below the colored cell
- ✅ Leave empty cells minimal

---

## 📊 **Change Metadata**

For each detected change, the tool records:

```json
{
  "change_id": "CHANGE_ABC123DE",
  "type": "NEW",
  "content": "Add vision coverage",
  "context": {
    "before": "Coverage types include:",
    "current": "Add vision coverage",
    "after": "Preventive services at 100%"
  },
  "source": {
    "sheet": "Medical",
    "row": 5,
    "column": 2,
    "cell_ref": "B5"
  },
  "detected_at": "2026-04-07T15:30:00Z"
}
```

---

## 🎓 **Quick Tips**

1. **Start Simple** - Use just 2 columns (Current | Updated) and highlight the changes
2. **Be Descriptive** - Write complete sentences in colored cells
3. **Add Context** - Include surrounding text for understanding
4. **Use Multiple Sheets** - Organize by policy type (Medical, Dental, Vision, etc.)
5. **Review Before Approving** - The tool shows changes for your approval before applying
6. **Edit as Needed** - You can refine the wording in the dashboard before applying

---

**No specific format required! Just highlight what changed and the tool handles the rest.** ✨
