"""Production-grade Streamlit dashboard for CreditPolicyIQ."""
import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

# Page configuration
st.set_page_config(
    page_title="CreditPolicyIQ - Policy Automation",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        "About": "CreditPolicyIQ - Intelligent Credit Policy Automation Tool",
    }
)

# API Configuration
API_BASE_URL = "http://localhost:8000/api"
REQUEST_TIMEOUT = 10

# Custom CSS for production look
st.markdown("""
<style>
    /* Main container */
    .main {
        padding: 0;
    }

    /* Header styling */
    .header-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 30px;
        border-radius: 0;
        margin-bottom: 30px;
    }

    .header-container h1 {
        margin: 0;
        font-size: 32px;
        font-weight: bold;
    }

    .header-container p {
        margin: 5px 0 0 0;
        font-size: 14px;
        opacity: 0.9;
    }

    /* Section styling */
    .section-container {
        background: white;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        padding: 25px;
        margin-bottom: 20px;
    }

    .section-title {
        font-size: 18px;
        font-weight: 600;
        margin-bottom: 15px;
        color: #333;
        display: flex;
        align-items: center;
        gap: 10px;
    }

    /* Status indicators */
    .status-success {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 12px;
        border-radius: 4px;
        margin: 10px 0;
    }

    .status-warning {
        background: #fff3cd;
        border: 1px solid #ffeaa7;
        color: #856404;
        padding: 12px;
        border-radius: 4px;
        margin: 10px 0;
    }

    .status-error {
        background: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        padding: 12px;
        border-radius: 4px;
        margin: 10px 0;
    }

    /* Button styling */
    .stButton > button {
        border-radius: 4px;
        font-weight: 500;
    }

    /* File info */
    .file-info {
        background: #f8f9fa;
        padding: 12px;
        border-radius: 4px;
        margin: 10px 0;
        border-left: 4px solid #667eea;
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
        return False, f"Request timeout after {REQUEST_TIMEOUT} seconds"
    except Exception as e:
        return False, str(e)


def check_master_exists() -> bool:
    """Check if master document exists."""
    success, data = api_call("GET", "/master/current-status")
    return success and data.get("exists", False)


def get_master_info() -> Dict[str, Any]:
    """Get master document info."""
    success, data = api_call("GET", "/master/current-status")
    if success:
        return data
    return {}


# ============================================================================
# HEADER
# ============================================================================

st.markdown("""
<div class="header-container">
    <h1>🏛️ CreditPolicyIQ</h1>
    <p>Intelligent Credit Policy Automation & Change Management</p>
</div>
""", unsafe_allow_html=True)

# ============================================================================
# MAIN CONTENT - TABS
# ============================================================================

tab1, tab2, tab3, tab4 = st.tabs(["📤 Upload", "🔍 Review", "✅ Apply", "⚙️ Settings"])

# ============================================================================
# TAB 1: UPLOAD
# ============================================================================
with tab1:
    st.markdown('<div class="section-container">', unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1], gap="medium")

    # LEFT COLUMN: Master Document
    with col1:
        st.markdown('<div class="section-title">📄 Master Policy Document</div>', unsafe_allow_html=True)

        master_info = get_master_info()
        if master_info.get("exists"):
            file_size = master_info.get("size", 0) / (1024 * 1024)
            st.markdown(f"""
            <div class="file-info">
                ✅ <b>Master Document Loaded</b><br>
                Size: {file_size:.2f} MB<br>
                Updated: {master_info.get('modified', 'Unknown')}
            </div>
            """, unsafe_allow_html=True)

            if st.button("📥 Download Master", key="download_master", use_container_width=True):
                success, data = api_call("GET", "/master/current")
                if success:
                    st.download_button(
                        label="Download Master Document",
                        data=data,
                        file_name="master_policy.docx",
                        key="download_button"
                    )
        else:
            st.info("📭 No master document uploaded yet")

        st.markdown("---")
        st.markdown("**Upload Master Document**")
        master_file = st.file_uploader(
            "Choose a Word document (.docx)",
            type=["docx"],
            key="master_uploader"
        )

        if master_file:
            if st.button("⬆️ Upload Master", use_container_width=True, key="upload_master_btn"):
                with st.spinner("Uploading master document..."):
                    file_bytes = master_file.getvalue()
                    files = {"file": ("master_policy.docx", file_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
                    success, response = api_call("POST", "/upload-master", files=files)

                    if success:
                        st.markdown("""
                        <div class="status-success">
                            ✅ Master document uploaded successfully!
                        </div>
                        """, unsafe_allow_html=True)
                        st.rerun()
                    else:
                        st.markdown(f"""
                        <div class="status-error">
                            ❌ Upload failed: {response}
                        </div>
                        """, unsafe_allow_html=True)

    # RIGHT COLUMN: Technical Document
    with col2:
        st.markdown('<div class="section-title">📋 Technical Document (Changes)</div>', unsafe_allow_html=True)
        st.markdown("Upload Excel (.xlsx) or Word (.docx) file with highlighted changes")

        doc_type = st.radio(
            "Document Format",
            ["Excel (Recommended)", "Word Document"],
            key="doc_type_selector"
        )

        if doc_type == "Excel (Recommended)":
            file_types = ["xlsx"]
            description = "Choose Excel file (.xlsx)"
            api_endpoint = "/upload-excel"
            content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        else:
            file_types = ["docx"]
            description = "Choose Word file (.docx)"
            api_endpoint = "/upload-technical-document"
            content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

        tech_file = st.file_uploader(
            description,
            type=file_types,
            key="tech_uploader"
        )

        if tech_file:
            st.markdown(f"""
            <div class="file-info">
                📎 {tech_file.name}<br>
                Size: {tech_file.size / 1024:.1f} KB
            </div>
            """, unsafe_allow_html=True)

            if st.button("🔍 Detect Changes", use_container_width=True, key="detect_changes_btn"):
                if not check_master_exists():
                    st.markdown("""
                    <div class="status-warning">
                        ⚠️ Master document not found. Please upload master document first.
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    with st.spinner("Analyzing document for changes..."):
                        file_bytes = tech_file.getvalue()
                        files = {"file": (tech_file.name, file_bytes, content_type)}
                        success, response = api_call("POST", api_endpoint, files=files)

                        if success:
                            total_changes = response.get("total_changes", 0)
                            st.markdown(f"""
                            <div class="status-success">
                                ✅ Detection complete!<br>
                                Found <b>{total_changes}</b> changes
                            </div>
                            """, unsafe_allow_html=True)
                            st.rerun()
                        else:
                            st.markdown(f"""
                            <div class="status-error">
                                ❌ Detection failed: {response}
                            </div>
                            """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


# ============================================================================
# TAB 2: REVIEW CHANGES
# ============================================================================
with tab2:
    st.markdown('<div class="section-container">', unsafe_allow_html=True)

    st.markdown('<div class="section-title">🔍 Review Detected Changes</div>', unsafe_allow_html=True)

    # Get pending changes
    success, changes_data = api_call("GET", "/changes/pending")

    if not success or not changes_data.get("changes"):
        st.info("📭 No changes detected. Upload a technical document to get started.")
    else:
        changes = changes_data.get("changes", [])
        st.markdown(f"**Total Changes:** {len(changes)}")

        for idx, change in enumerate(changes):
            with st.container(border=True):
                change_type = change.get("Change_Type", "CHANGE")
                change_id = change.get("change_id", f"Change_{idx}")

                # Color indicator
                if change_type == "NEW":
                    indicator = "🟢 NEW"
                elif change_type == "MODIFIED":
                    indicator = "🟡 MODIFIED"
                elif change_type == "DELETED":
                    indicator = "🔴 DELETED"
                else:
                    indicator = "🔵 REVIEW TYPE"

                col_indicator, col_type = st.columns([2, 1])
                with col_indicator:
                    st.markdown(f"**{indicator}** - {change_id}")

                # Type selector if needed
                if change_type == "CHANGE":
                    with col_type:
                        selected_type = st.selectbox(
                            "Type",
                            ["NEW", "MODIFIED", "DELETED"],
                            key=f"type_{idx}",
                            label_visibility="collapsed"
                        )
                        if selected_type:
                            change["Change_Type"] = selected_type

                # Content
                content = change.get("Policy_Content", "")
                st.markdown("**Content:**")
                st.code(content, language="text")

                # Mapping info
                mapping = change.get("mapping", {})
                if mapping:
                    confidence = mapping.get("confidence", 0)
                    section = mapping.get("section_title", "Unknown")
                    st.caption(f"📍 Maps to: **{section}** ({confidence:.0%} confidence)")

                # Action buttons
                col1, col2, col3 = st.columns(3)
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
                    if st.button("✏️ Edit", key=f"edit_{idx}", use_container_width=True):
                        st.info("Edit functionality coming soon")

                with col3:
                    if st.button("❌ Reject", key=f"reject_{idx}", use_container_width=True):
                        success, _ = api_call("POST", f"/changes/{change_id}/reject", {
                            "reason": "Rejected by reviewer"
                        })
                        if success:
                            st.error("❌ Rejected!")
                            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


# ============================================================================
# TAB 3: APPLY CHANGES
# ============================================================================
with tab3:
    st.markdown('<div class="section-container">', unsafe_allow_html=True)

    st.markdown('<div class="section-title">✅ Apply Changes to Master</div>', unsafe_allow_html=True)

    # Get approved changes
    success, approvals_data = api_call("GET", "/changes/pending")
    approved_count = 0
    if success:
        changes = approvals_data.get("changes", [])
        approved_count = len([c for c in changes if c.get("status") == "APPROVED"])

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Approved Changes", approved_count)
    with col2:
        st.metric("Pending Review", "—")
    with col3:
        st.metric("Applied Changes", "—")

    st.markdown("---")

    if approved_count > 0:
        st.markdown(f"**Ready to apply {approved_count} changes to master document**")

        if st.button("🚀 Apply All Changes", use_container_width=True, type="primary"):
            with st.spinner("Applying changes..."):
                success, result = api_call("POST", "/master/apply-changes")

                if success:
                    applied = result.get("applied_count", 0)
                    total = result.get("total_approved", 0)
                    st.markdown(f"""
                    <div class="status-success">
                        ✅ Changes applied successfully!<br>
                        Applied: {applied}/{total} changes<br>
                        New version created
                    </div>
                    """, unsafe_allow_html=True)
                    st.rerun()
                else:
                    st.markdown(f"""
                    <div class="status-error">
                        ❌ Failed to apply changes: {result}
                    </div>
                    """, unsafe_allow_html=True)
    else:
        st.info("No approved changes to apply. Review and approve changes first.")

    st.markdown('</div>', unsafe_allow_html=True)


# ============================================================================
# TAB 4: SETTINGS
# ============================================================================
with tab4:
    st.markdown('<div class="section-container">', unsafe_allow_html=True)

    st.markdown('<div class="section-title">⚙️ Settings & Configuration</div>', unsafe_allow_html=True)

    # LLM Configuration
    st.subheader("LLM Provider")
    col1, col2 = st.columns(2)
    with col1:
        provider = st.selectbox(
            "Provider",
            ["Mock (No API Key)", "Anthropic", "OpenAI"],
            help="Select LLM provider for policy translation"
        )

    if provider != "Mock (No API Key)":
        with col2:
            api_key = st.text_input(
                "API Key",
                type="password",
                help="Your API key for the selected provider"
            )

    st.markdown("---")

    # Application Info
    st.subheader("Application Info")
    st.markdown(f"""
    - **Version:** 1.0.0
    - **API Base:** {API_BASE_URL}
    - **Data Directory:** data/
    - **Status:** ✅ Ready
    """)

    # Links
    st.markdown("---")
    st.subheader("Resources")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("[📖 Documentation](https://github.com/SinduDeva/creditpolicyiq)")
    with col2:
        st.markdown("[🐛 Report Issues](https://github.com/SinduDeva/creditpolicyiq/issues)")
    with col3:
        st.markdown("[⚡ Quick Start](./QUICKSTART.md)")

    st.markdown('</div>', unsafe_allow_html=True)
