# LLM Provider Configuration Guide

This guide explains how to configure different LLM providers and understand which features work without an LLM API.

---

## Quick Overview

The Credit Policy Automation Tool supports multiple LLM providers:

| Provider | Status | Cost | Setup |
|----------|--------|------|-------|
| **Anthropic** | ✅ Default (Recommended) | $0.003/1K input tokens | API Key required |
| **OpenAI** | ✅ Supported | $0.03/1K input tokens | API Key + install openai |
| **Mock** | ✅ Always Available | FREE | No API key needed |

---

## Features That Work Without LLM API

✅ **NO LLM API KEY REQUIRED** for these features:

### Core Functionality
- ✅ Upload Excel files with policy changes
- ✅ Parse Excel with color detection (GREEN/YELLOW/RED)
- ✅ Extract Word document structure
- ✅ Detect changes in master document
- ✅ Calculate confidence scores for change matching
- ✅ Approve/reject changes manually
- ✅ Apply approved changes to master document
- ✅ Version control and document management
- ✅ View audit logs and change history
- ✅ Download master document

### API Endpoints
- ✅ POST /api/upload-excel
- ✅ GET /api/master/current
- ✅ GET /api/master/versions
- ✅ GET /api/changes/pending
- ✅ POST /api/changes/{id}/approve
- ✅ POST /api/changes/{id}/reject
- ✅ POST /api/master/apply-changes
- ✅ GET /api/logs/changes
- ✅ GET /api/logs/approvals
- ✅ GET /api/health

### Dashboard Pages
- ✅ Dashboard (metrics & recent changes)
- ✅ Upload Excel
- ✅ Review Changes (without AI suggestions)
- ✅ Approve Changes
- ✅ Master Document
- ✅ Version History
- ✅ Logs

---

## Features That Require LLM

⚠️ **REQUIRES LLM API KEY** for these features:

### Enhanced Functionality
- ⚠️ Automatic translation of changes to Word narrative format
- ⚠️ LLM-powered suggestions for policy wording
- ⚠️ Confidence scoring from LLM analysis
- ⚠️ Format recommendations (paragraph vs bullet vs table)

### Endpoint
- ⚠️ POST /api/changes/{id}/translate (with AI suggestion)

### Dashboard
- ⚠️ Review Changes page (with LLM suggestions)
- ⚠️ Auto-generated change narratives

---

## Configuration Options

### Option 1: Use Anthropic (Recommended)

**Step 1: Get API Key**
```bash
# Visit https://console.anthropic.com/
# Create an API key (free $5 credit available)
```

**Step 2: Configure**
```bash
# Copy configuration
cp .env.example .env

# Edit .env
LLM_PROVIDER=anthropic
LLM_API_KEY=sk-ant-xxx...
LLM_MODEL=claude-3-5-sonnet-20241022
```

**Step 3: Start**
```bash
./run_all.sh
```

### Option 2: Use OpenAI

**Step 1: Get API Key**
```bash
# Visit https://platform.openai.com/account/api-keys
# Create an API key
```

**Step 2: Install OpenAI Package**
```bash
pip install openai==1.3.0
# Or uncomment in requirements.txt and reinstall
```

**Step 3: Configure**
```bash
# Edit .env
LLM_PROVIDER=openai
LLM_API_KEY=sk-xxx...
LLM_MODEL=gpt-4-turbo
```

**Step 4: Start**
```bash
./run_all.sh
```

### Option 3: Use Mock Provider (Testing Only)

**No API key needed!** Uses built-in mock provider.

**Configure**
```bash
# Edit .env
LLM_PROVIDER=mock
# LLM_API_KEY is not required
```

**Start**
```bash
./run_all.sh
```

**Note**: Mock provider generates simple narratives without real AI. Use for testing only.

---

## Environment Variables

### LLM Configuration

```bash
# Choose provider: anthropic, openai, or mock
LLM_PROVIDER=anthropic

# API key for the selected provider
# For Anthropic: https://console.anthropic.com/
# For OpenAI: https://platform.openai.com/account/api-keys
LLM_API_KEY=your-api-key-here

# Model name (defaults based on provider if not specified)
# Anthropic: claude-3-5-sonnet-20241022 (default)
# OpenAI: gpt-4-turbo (default)
LLM_MODEL=claude-3-5-sonnet-20241022

# Maximum tokens for LLM responses
LLM_MAX_TOKENS=1000

# Backward compatibility (Anthropic-specific)
# ANTHROPIC_API_KEY=your-key-here  # Alternative to LLM_API_KEY
```

---

## Model Recommendations

### Anthropic

**Recommended: claude-3-5-sonnet-20241022**
- Best balance of cost and quality
- Excellent for policy language
- Fastest response times
- ~$0.003/1K tokens input

**Alternative: claude-3-opus-20240229**
- More powerful but slower
- Better for complex analysis
- ~$0.015/1K tokens input

### OpenAI

**Recommended: gpt-4-turbo**
- Excellent quality
- Good for policy analysis
- ~$0.03/1K tokens input

**Alternative: gpt-4**
- Most powerful
- Slower responses
- ~$0.03/1K tokens input

**Budget: gpt-3.5-turbo**
- Fastest and cheapest
- Good for simple translations
- ~$0.0005/1K tokens input

---

## Graceful Degradation

The app automatically falls back gracefully:

```
┌─ User requests translation
│
├─ Check if API key configured
│
├─ YES → Call configured provider (Anthropic/OpenAI)
│  ├─ Success → Return AI suggestion
│  └─ Failure → Fall back to mock provider
│
└─ NO → Use mock provider automatically
   └─ Generate simple mock suggestion
```

**Result**: App always works, but without API key you get mock suggestions.

---

## Cost Estimation

### Anthropic (claude-3-5-sonnet)
- ~100 tokens per policy change translation
- Cost per change: ~$0.0003 (0.03 cents)
- 100 translations: ~$0.03
- 1000 translations: ~$0.30

### OpenAI (gpt-4-turbo)
- ~100 tokens per policy change translation
- Cost per change: ~$0.003 (0.3 cents)
- 100 translations: ~$0.30
- 1000 translations: ~$3.00

### Free Option (Mock Provider)
- Cost: **$0**
- Good for: Testing, learning, small deployments
- Note: Suggestions are generated without real AI

---

## Troubleshooting

### Error: "No module named 'anthropic'"

**Solution**: Install Anthropic package
```bash
pip install anthropic==0.7.1
```

### Error: "No module named 'openai'"

**Solution**: Install OpenAI package
```bash
pip install openai==1.3.0
```

### Error: "API key not configured"

**Solution**: 
```bash
# Set environment variable
export LLM_API_KEY="your-key-here"

# Or edit .env file
LLM_API_KEY=your-key-here

# Or use mock provider (no key needed)
LLM_PROVIDER=mock
```

### Error: "Authentication failed"

**Solution**: 
- Verify API key is correct (copy from provider's console)
- Check for extra spaces or quotes in .env
- Ensure key has proper permissions/scopes

### LLM suggestions seem basic/generic

**Likely cause**: Using mock provider (no API configured)

**Solution**:
```bash
# Set up real API key
export LLM_API_KEY="sk-..."
export LLM_PROVIDER="anthropic"
```

---

## Testing Without API Key

### Full App Test (No LLM)

```bash
# 1. Set mock provider
export LLM_PROVIDER=mock

# 2. Start app
./run_all.sh

# 3. Test all features:
# - Upload Excel: Works ✅
# - Review Changes: Works (without AI) ✅
# - Approve/Reject: Works ✅
# - Apply Changes: Works ✅
# - Download Document: Works ✅
```

### Partial Test (With LLM)

```bash
# 1. Set API key
export LLM_API_KEY="your-key"
export LLM_PROVIDER="anthropic"

# 2. Start app
./run_all.sh

# 3. Test LLM features:
# - Translate Changes: Works with AI ✅
# - Get Suggestions: AI-generated ✅
```

---

## Switching Providers

### From Anthropic to OpenAI

```bash
# Update .env
LLM_PROVIDER=openai
LLM_API_KEY=sk-xxx...  # OpenAI key
LLM_MODEL=gpt-4-turbo

# Restart app
./run_all.sh
```

### From OpenAI to Mock (Disable LLM)

```bash
# Update .env
LLM_PROVIDER=mock
# LLM_API_KEY not needed

# Restart app
./run_all.sh
```

---

## API Response Examples

### With Anthropic/OpenAI API

```json
{
  "suggested_narrative": "The minimum CIBIL score requirement has been enhanced to 750 to strengthen our risk assessment framework...",
  "format_type": "paragraph",
  "confidence_score": 0.95,
  "reasoning": "Technical change in minimum CIBIL threshold matches policy domain conventions..."
}
```

### With Mock Provider (No API)

```json
{
  "suggested_narrative": "Policy section Credit Eligibility: Updated to reflect new CIBIL requirements.",
  "format_type": "narrative",
  "confidence_score": 0.5,
  "reasoning": "Generated by mock provider (no LLM API). Please review carefully.",
  "is_mock": true
}
```

---

## Production Deployment

### Recommended Setup

```env
# Production - Use real LLM
LLM_PROVIDER=anthropic
LLM_API_KEY=${ANTHROPIC_API_KEY}  # Use secrets management
LLM_MODEL=claude-3-5-sonnet-20241022
LLM_MAX_TOKENS=1000
```

### Cost Management

```env
# Budget-conscious setup
LLM_PROVIDER=openai
LLM_MODEL=gpt-3.5-turbo  # Cheapest option
LLM_MAX_TOKENS=500       # Reduce token usage
```

### High Quality Setup

```env
# Quality-focused setup
LLM_PROVIDER=anthropic
LLM_MODEL=claude-3-opus-20240229  # Most capable
LLM_MAX_TOKENS=2000               # Allow longer responses
```

---

## Summary

| Scenario | Configuration | Cost | Recommendation |
|----------|---------------|------|-----------------|
| **Full testing** | LLM_PROVIDER=mock | FREE | ✅ Start here |
| **Production** | LLM_PROVIDER=anthropic | Low | ✅ Recommended |
| **Cost sensitive** | LLM_PROVIDER=openai + gpt-3.5-turbo | Very Low | ✅ Good |
| **High quality** | LLM_PROVIDER=anthropic + claude-opus | Low | ✅ Best quality |

---

**The app works great without an LLM API!** Use mock provider for testing, add API key when you want AI-powered suggestions.
