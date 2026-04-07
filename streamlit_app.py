"""Production-grade Streamlit dashboard for CreditPolicyIQ - Unified Single Window."""
import streamlit as st
import requests
from datetime import datetime
from typing import Dict, Any, Optional

# Page configuration
st.set_page_config(
    page_title="CreditPolicyIQ - Policy Automation",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# API Configuration
API_BASE_URL = "http://localhost:8000/api"
REQUEST_TIMEOUT = 10

# Custom CSS for production look
st.markdown("""
<style>
    /* Remove padding */
    .main {
        padding: 0;
    }

    /* Header */
    .header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 40px 30px;
        margin-bottom: 30px;
        border-radius: 0;
    }

    .header h1 {
        margin: 0;
        font-size: 36px;
        font-weight: bold;
    }

    .header p {
        margin: 8px 0 0 0;
        font-size: 14px;
        opacity: 0.9;
    }

    /* Section container */
    .section {
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 25px;
        margin: 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }

    .section-title {
        font-size: 18px;
        font-weight: 600;
        margin-bottom: 20px;
        color: #333;
        display: flex;
        align-items: center;
        gap: 10px;
        border-bottom: 2px solid #667eea;
        padding-bottom: 10px;
    }

    /* Status boxes */
    .status-box {
        padding: 15px;
        border-radius: 6px;
        margin: 10px 0;
        border-left: 4px solid;
    }

    .status-success {
        background: #d4edda;
        border-left-color: #28a745;
        color: #155724;
    }

    .status-warning {
        background: #fff3cd;
        border-left-color: #ffc107;
        color: #856404;
    }

    .status-error {
        background: #f8d7da;
        border-left-color: #dc3545;
        color: #721c24;
    }

    .status-info {
        background: #d1ecf1;
        border-left-color: #17a2b8;
        color: #0c5460;
    }

    /* File info card */
    .file-card {
        background: #f8f9fa;
        padding: 12px;
        border-radius: 6px;
        margin: 10px 0;
        border-left: 4px solid #667eea;
        font-size: 14px;
    }

    /* Buttons */
    .stButton > button {
        border-radius: 6px;
        font-weight: 500;
        transition: all 0.3s;
    }

    /* Change item */
    .change-item {
        background: #f8f9fa;
        border: 1px solid #e0e0e0;
        border-radius: 6px;
        padding: 15px;
        margin: 10px 0;
    }

    .change-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 10px;
        font-weight: 600;
    }

    /* Metrics */
    .metric-box {
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 6px;
        padding: 15px;
        text-align: center;
    }

    .metric-value {
        font-size: 28px;
        font-weight: bold;
        color: #667eea;
    }

    .metric-label {
        font-size: 12px;
        color: #666;
        margin-top: 5px;
    }

    /* Divider */
    .divider {
        margin: 30px 0;
        border-top: 2px solid #f0f0f0;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def api_call(
    method: str, endpoint: str, json_data: Optional[Dict] = None, files: Optional[Dict] = None
) -> tuple[bool, Any]:
    """Make API call and handle errors."""
    try:
        url = f"{API_BASE_URL}{endpoint}"

        if method == "GET":
            response = requests.get(url, timeout=REQUEST_TIMEOUT)
        elif method == "POST":
            if files:
                response = requests.post(url, files=files, timeout=REQUEST_TIMEOUT)
            else:
                response = requests.post(url, json=json_data, timeout=REQUEST_TIMEOUT)
        else:
            return False, "Unsupported HTTP method"

        if response.status_code == 200:
            try:
                return True, response.json()
            except ValueError:
                return True, response.content
        else:
            error_msg = response.text or f"HTTP {response.status_code}"
            return False, error_msg

    except requests.exceptions.ConnectionError:
        return False, "Cannot connect to API server"
    except requests.exceptions.Timeout:
        return False, f"Request timeout"
    except Exception as e:
        return False, str(e)


def check_master_exists() -> bool:
    """Check if master document exists."""
    success, data = api_call("GET", "/master/current-status")
    return success and data.get("exists", False)


def get_master_info() -> Dict[str, Any]:
    """Get master document info."""
    success, data = api_call("GET", "/master/current-status")
    return data if success else {}


# ============================================================================
# HEADER
# ============================================================================

st.markdown("""
<div class="header">
    <h1>🏛️ CreditPolicyIQ</h1>
    <p>Intelligent Credit Policy Automation & Change Management</p>
</div>
""", unsafe_allow_html=True)

# ============================================================================
# MAIN UNIFIED INTERFACE
# ============================================================================

st.markdown('<div style="padding: 0 20px;">', unsafe_allow_html=True)

# ============================================================================
# SECTION 1: UPLOAD & MASTER DOCUMENT
# ============================================================================
st.markdown('<div class="section">', unsafe_allow_html=True)
st.markdown('<div class="section-title">📄 Step 1: Upload Documents</div>', unsafe_allow_html=True)

col_master, col_tech = st.columns([1, 1], gap="medium")

# Master Document
with col_master:
    st.markdown("**Master Policy Document**")

    master_info = get_master_info()
    if master_info.get("exists"):
        file_size = master_info.get("size", 0) / (1024 * 1024)
        st.markdown(f"""
        <div class="status-box status-success">
            ✅ Master document loaded<br>
            <small>Size: {file_size:.2f} MB</small>
        </div>
        """, unsafe_allow_html=True)

        if st.button("📥 Download Master", use_container_width=True):
            success, data = api_call("GET", "/master/current")
            if success:
                st.download_button(
                    label="Download",
                    data=data,
                    file_name="master_policy.docx",
                    use_container_width=True
                )
    else:
        st.markdown("""
        <div class="status-box status-info">
            ℹ️ No master document uploaded
        </div>
        """, unsafe_allow_html=True)

    master_file = st.file_uploader(
        "Upload Master (.docx)",
        type=["docx"],
        key="master_uploader",
        label_visibility="collapsed"
    )

    if master_file:
        col_upload, col_info = st.columns([2, 1])
        with col_upload:
            if st.button("⬆️ Upload Master", use_container_width=True, key="upload_master"):
                with st.spinner("Uploading..."):
                    file_bytes = master_file.getvalue()
                    files = {"file": ("master_policy.docx", file_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
                    success, response = api_call("POST", "/upload-master", files=files)

                    if success:
                        st.markdown("""
                        <div class="status-box status-success">
                            ✅ Master document uploaded!
                        </div>
                        """, unsafe_allow_html=True)
                        st.rerun()
                    else:
                        st.markdown(f"""
                        <div class="status-box status-error">
                            ❌ Upload failed
                        </div>
                        """, unsafe_allow_html=True)
        with col_info:
            st.caption(f"{master_file.size / 1024:.0f} KB")

# Technical Document
with col_tech:
    st.markdown("**Technical Document (Changes)**")

    if not check_master_exists():
        st.markdown("""
        <div class="status-box status-warning">
            ⚠️ Upload master document first
        </div>
        """, unsafe_allow_html=True)
        st.info("Master document required to detect changes")
    else:
        st.markdown("""
        <div class="status-box status-info">
            ℹ️ Ready to upload technical document
        </div>
        """, unsafe_allow_html=True)

        doc_type = st.radio(
            "Format",
            ["Excel (.xlsx)", "Word (.docx)"],
            horizontal=True,
            key="doc_type",
            label_visibility="collapsed"
        )

        if doc_type == "Excel (.xlsx)":
            file_types = ["xlsx"]
            endpoint = "/upload-excel"
            content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        else:
            file_types = ["docx"]
            endpoint = "/upload-technical-document"
            content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

        tech_file = st.file_uploader(
            f"Upload {doc_type}",
            type=file_types,
            key="tech_uploader",
            label_visibility="collapsed"
        )

        if tech_file:
            col_upload, col_info = st.columns([2, 1])
            with col_upload:
                if st.button("🔍 Detect Changes", use_container_width=True, key="detect_btn"):
                    with st.spinner("Analyzing..."):
                        file_bytes = tech_file.getvalue()
                        files = {"file": (tech_file.name, file_bytes, content_type)}
                        success, response = api_call("POST", endpoint, files=files)

                        if success:
                            total = response.get("total_changes", 0)
                            st.markdown(f"""
                            <div class="status-box status-success">
                                ✅ Detection complete<br>
                                Found <b>{total} changes</b>
                            </div>
                            """, unsafe_allow_html=True)
                            st.rerun()
                        else:
                            st.markdown(f"""
                            <div class="status-box status-error">
                                ❌ Detection failed
                            </div>
                            """, unsafe_allow_html=True)
            with col_info:
                st.caption(f"{tech_file.size / 1024:.0f} KB")

st.markdown('</div>', unsafe_allow_html=True)

# ============================================================================
# DIVIDER
# ============================================================================
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ============================================================================
# SECTION 2: REVIEW CHANGES
# ============================================================================
success, changes_data = api_call("GET", "/changes/pending")
changes = changes_data.get("changes", []) if success else []

st.markdown('<div class="section">', unsafe_allow_html=True)
st.markdown('<div class="section-title">🔍 Step 2: Review & Approve Changes</div>', unsafe_allow_html=True)

if not changes:
    st.markdown("""
    <div class="status-box status-info">
        ℹ️ No changes detected yet. Upload a technical document to get started.
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown(f"**{len(changes)} changes detected**")

    for idx, change in enumerate(changes):
        st.markdown(f'<div class="change-item">', unsafe_allow_html=True)

        change_type = change.get("Change_Type", "CHANGE")
        change_id = change.get("change_id", f"Change_{idx}")

        # Determine icon
        if change_type == "NEW":
            icon = "🟢"
        elif change_type == "MODIFIED":
            icon = "🟡"
        elif change_type == "DELETED":
            icon = "🔴"
        else:
            icon = "🔵"

        col_header, col_actions = st.columns([2, 1])

        with col_header:
            st.markdown(f"**{icon} {change_type}** - {change_id}")

            # Type selector for CHANGE type
            if change_type == "CHANGE":
                selected_type = st.selectbox(
                    "Select type",
                    ["NEW", "MODIFIED", "DELETED"],
                    key=f"type_{idx}",
                    label_visibility="collapsed"
                )
                if selected_type and selected_type != "CHANGE":
                    change["Change_Type"] = selected_type

        # Content
        content = change.get("Policy_Content", "")
        st.markdown(f"```\n{content}\n```")

        # Mapping
        mapping = change.get("mapping", {})
        if mapping:
            confidence = mapping.get("confidence", 0)
            section = mapping.get("section_title", "Unknown")
            st.caption(f"📍 Maps to: **{section}** ({confidence:.0%} confidence)")

        # Buttons
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button("✅ Accept", key=f"accept_{idx}", use_container_width=True):
                success, _ = api_call("POST", f"/changes/{change_id}/approve", {
                    "user": "reviewer",
                    "comment": "Approved",
                    "change_type": change.get("Change_Type", change_type)
                })
                if success:
                    st.success("✅ Accepted!")
                    st.rerun()

        with col2:
            if st.button("❌ Reject", key=f"reject_{idx}", use_container_width=True):
                success, _ = api_call("POST", f"/changes/{change_id}/reject", {
                    "reason": "Rejected by reviewer"
                })
                if success:
                    st.error("❌ Rejected!")
                    st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# ============================================================================
# DIVIDER
# ============================================================================
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ============================================================================
# SECTION 3: APPLY CHANGES
# ============================================================================
st.markdown('<div class="section">', unsafe_allow_html=True)
st.markdown('<div class="section-title">✅ Step 3: Apply Changes to Master</div>', unsafe_allow_html=True)

# Get approved changes count
approved_count = len([c for c in changes if c.get("status") == "APPROVED"]) if changes else 0

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(f'<div class="metric-box"><div class="metric-value">{approved_count}</div><div class="metric-label">Approved</div></div>', unsafe_allow_html=True)
with col2:
    st.markdown(f'<div class="metric-box"><div class="metric-value">{len(changes) - approved_count}</div><div class="metric-label">Pending</div></div>', unsafe_allow_html=True)
with col3:
    st.markdown(f'<div class="metric-box"><div class="metric-value">0</div><div class="metric-label">Applied</div></div>', unsafe_allow_html=True)

st.markdown("---")

if approved_count > 0:
    st.markdown(f"**Ready to apply {approved_count} changes**")

    if st.button("🚀 Apply All Changes", use_container_width=True, type="primary"):
        with st.spinner("Applying changes..."):
            success, result = api_call("POST", "/master/apply-changes")

            if success:
                applied = result.get("applied_count", 0)
                total = result.get("total_approved", 0)
                st.markdown(f"""
                <div class="status-box status-success">
                    ✅ Changes applied successfully!<br>
                    Applied: <b>{applied}/{total}</b> changes<br>
                    New version created
                </div>
                """, unsafe_allow_html=True)
                st.rerun()
            else:
                st.markdown(f"""
                <div class="status-box status-error">
                    ❌ Failed to apply changes
                </div>
                """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div class="status-box status-info">
        ℹ️ No approved changes to apply
    </div>
    """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# ============================================================================
# FOOTER
# ============================================================================
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 12px; padding: 20px;">
    CreditPolicyIQ v1.0.0 | <a href="#">Documentation</a> | <a href="#">Support</a>
</div>
""", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)
