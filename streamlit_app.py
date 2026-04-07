"""Interactive Streamlit dashboard for CreditPolicyIQ."""
import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from typing import Dict, Any, Optional, List

# Page configuration
st.set_page_config(
    page_title="Credit Policy Automation POC",
    layout="wide",
    initial_sidebar_state="expanded",
)

# API Configuration
API_BASE_URL = "http://localhost:8000/api"
REQUEST_TIMEOUT = 10

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================


def api_call(
    method: str, endpoint: str, json_data: Optional[Dict] = None, files: Optional[Dict] = None
) -> tuple[bool, Any]:
    """
    Make API call and handle errors.

    Args:
        method: HTTP method (GET, POST, etc.)
        endpoint: API endpoint path
        json_data: JSON body data
        files: Files to upload (dict with file objects, bytes, or tuples)

    Returns:
        Tuple of (success, response_data)
    """
    try:
        url = f"{API_BASE_URL}{endpoint}"
        headers = {}

        if method == "GET":
            response = requests.get(url, timeout=REQUEST_TIMEOUT)
        elif method == "POST":
            if files:
                # Files can be passed directly - requests handles:
                # - file objects with .read()
                # - tuples: (filename, fileobj, content_type)
                # - bytes are wrapped: (filename, bytes, content_type)
                response = requests.post(url, files=files, timeout=REQUEST_TIMEOUT)
            else:
                headers["Content-Type"] = "application/json"
                response = requests.post(
                    url, json=json_data, headers=headers, timeout=REQUEST_TIMEOUT
                )
        else:
            return False, "Unsupported HTTP method"

        if response.status_code == 200:
            try:
                return True, response.json()
            except ValueError:
                # If response is not JSON (e.g., file download), return raw content
                return True, response.content
        else:
            error_msg = response.text or f"HTTP {response.status_code}"
            return False, error_msg

    except requests.exceptions.ConnectionError:
        return False, "Cannot connect to API. Make sure FastAPI server is running on http://localhost:8000"
    except requests.exceptions.Timeout:
        return False, f"Request timeout after {REQUEST_TIMEOUT} seconds"
    except Exception as e:
        return False, str(e)


def display_metric(label: str, value: Any, delta: Optional[str] = None):
    """Display a metric in a column."""
    col1, col2 = st.columns([2, 1])
    with col1:
        st.metric(label, value, delta=delta)


# ============================================================================
# PAGE 1: DASHBOARD
# ============================================================================


def page_dashboard():
    """Dashboard page with metrics and recent changes."""
    st.title("📊 Dashboard")

    # Fetch data
    with st.spinner("Loading dashboard data..."):
        # Get pending changes
        success_pending, pending_data = api_call("GET", "/changes/pending")
        pending_count = pending_data.get("total_pending", 0) if success_pending else 0

        # Get changes log
        success_changes, changes_data = api_call("GET", "/logs/changes")
        total_changes = changes_data.get("total_entries", 0) if success_changes else 0

        # Get approvals log
        success_approvals, approvals_data = api_call("GET", "/logs/approvals")
        approved_count = approvals_data.get("total_entries", 0) if success_approvals else 0

    # Display metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("⏳ Pending Changes", pending_count)

    with col2:
        st.metric("📝 Total Changes", total_changes)

    with col3:
        st.metric("✅ Approved Changes", approved_count)

    with col4:
        st.metric("📚 Documents", "1")

    st.divider()

    # Display recent changes table
    st.subheader("Recent Changes")

    if success_pending and pending_data.get("changes"):
        changes_list = []
        for change in pending_data.get("changes", [])[:10]:  # Show last 10
            changes_list.append({
                "Change ID": change.get("change_id", "N/A")[:20],
                "Type": change.get("original_data", {}).get("Change_Type", "N/A"),
                "Section": change.get("original_data", {}).get("Section_Name", "N/A")[:30],
                "Status": change.get("status", "N/A"),
            })

        if changes_list:
            df = pd.DataFrame(changes_list)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No pending changes found.")
    else:
        st.error("Failed to load pending changes")


# ============================================================================
# PAGE 2: UPLOAD EXCEL
# ============================================================================


def page_upload_excel():
    """Upload Excel file with underwriting changes."""
    st.title("📤 Upload Excel Changes")

    st.write("Upload Excel file with underwriting policy changes")

    # Display required columns
    with st.expander("📋 Required Columns"):
        cols = [
            "Section_ID",
            "Section_Name",
            "Policy_Content",
            "UW_Technical_Details",
            "Status",
            "Color_Flag",
            "Notes",
        ]
        st.write(", ".join(cols))

    # File uploader
    uploaded_file = st.file_uploader("Choose Excel file", type=["xlsx"])

    if uploaded_file:
        st.info(f"Selected file: {uploaded_file.name}")

        if st.button("Upload and Parse", type="primary"):
            with st.spinner("Uploading and parsing Excel..."):
                success, result = api_call(
                    "POST",
                    "/upload-excel",
                    files={"file": (uploaded_file.name, uploaded_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
                )

            if success:
                st.success("✅ File uploaded successfully!")

                # Display summary
                col1, col2, col3, col4 = st.columns(4)
                summary = result.get("excel_summary", {})

                with col1:
                    st.metric("Total Changes", result.get("total_changes", 0))

                with col2:
                    st.metric("New Policies", summary.get("by_type", {}).get("NEW", 0))

                with col3:
                    st.metric("Modified", summary.get("by_type", {}).get("MODIFIED", 0))

                with col4:
                    st.metric("Deleted", summary.get("by_type", {}).get("DELETED", 0))

                # Display detected changes table
                st.subheader("Detected Changes")
                changes = result.get("changes", [])

                if changes:
                    changes_list = []
                    for change in changes:
                        changes_list.append({
                            "Change ID": change.get("change_id", "N/A")[:20],
                            "Type": change.get("original_data", {}).get("Change_Type", "N/A"),
                            "Section": change.get("original_data", {}).get("Section_Name", "N/A")[:30],
                            "Confidence": f"{change.get('confidence_score', 0):.1%}",
                        })

                    df = pd.DataFrame(changes_list)
                    st.dataframe(df, use_container_width=True, hide_index=True)
                else:
                    st.info("No changes detected in file.")
            else:
                st.error(f"Failed to upload file: {result}")


# ============================================================================
# PAGE 3: REVIEW CHANGES
# ============================================================================


def page_review_changes():
    """Review and translate pending changes."""
    st.title("🔍 Review Changes")

    with st.spinner("Loading pending changes..."):
        success, data = api_call("GET", "/changes/pending")

    if not success:
        st.error(f"Failed to load pending changes: {data}")
        return

    pending_count = data.get("total_pending", 0)
    st.metric("Pending Changes", pending_count)

    if pending_count == 0:
        st.info("No pending changes to review.")
        return

    changes = data.get("changes", [])

    # Display each change in expandable cards
    for idx, change in enumerate(changes):
        change_id = change.get("change_id", f"Change_{idx}")
        status = change.get("status", "UNKNOWN")
        original = change.get("original_data", {})
        match = change.get("match_details", {})

        with st.expander(
            f"🔹 {original.get('Section_Name', 'Unknown')[:40]} - {status}", expanded=False
        ):
            col1, col2 = st.columns(2)

            with col1:
                st.write("**Excel Content:**")
                st.code(original.get("Policy_Content", "N/A"), language="text")

                st.write("**UW Technical Details:**")
                st.code(original.get("UW_Technical_Details", "N/A"), language="text")

            with col2:
                st.write("**Master Document Context:**")
                if match.get("matched"):
                    st.success(f"✅ Matched to: {match.get('section_title', 'Unknown')}")
                    st.write(f"Confidence: {match.get('similarity_score', 0):.1%}")
                else:
                    st.warning("⚠️ No matching section found")

            st.divider()

            # Status-specific actions
            if status == "PENDING":
                if st.button(
                    f"🤖 Translate with Claude", key=f"translate_{change_id}"
                ):
                    with st.spinner("Translating change..."):
                        success, result = api_call("POST", f"/changes/{change_id}/translate")

                    if success:
                        st.success("✅ Change translated!")
                        st.rerun()
                    else:
                        st.error(f"Translation failed: {result}")

            elif status == "PENDING_REVIEW":
                llm_result = change.get("llm_suggestion", {})

                st.write("**LLM Suggestion:**")
                st.text_area(
                    "Suggested Narrative",
                    value=llm_result.get("suggested_narrative", ""),
                    disabled=True,
                    height=150,
                    key=f"narrative_{change_id}",
                )

                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Confidence Score", f"{llm_result.get('confidence_score', 0):.1%}")

                with col2:
                    st.metric("Format Type", llm_result.get("format_type", "N/A"))

                with st.expander("📖 Reasoning"):
                    st.info(llm_result.get("reasoning", "No reasoning provided"))


# ============================================================================
# PAGE 4: APPROVE CHANGES
# ============================================================================


def page_approve_changes():
    """Approve or reject pending changes with edit option."""
    st.title("✅ Approve Changes")

    with st.spinner("Loading changes ready for approval..."):
        success, data = api_call("GET", "/changes/pending")

    if not success:
        st.error(f"Failed to load changes: {data}")
        return

    pending_changes = [
        c for c in data.get("changes", []) if c.get("status") == "PENDING_REVIEW"
    ]

    if not pending_changes:
        st.info("No changes ready for approval.")
        return

    st.metric("Changes Ready for Approval", len(pending_changes))

    for idx, change in enumerate(pending_changes):
        change_id = change.get("change_id", f"Change_{idx}")
        original = change.get("original_data", {})
        llm_result = change.get("llm_suggestion", {})
        was_edited = llm_result.get("was_edited", False)

        with st.expander(
            f"🔹 {original.get('Section_Name', 'Unknown')[:40]}" + (" [EDITED]" if was_edited else ""), expanded=False
        ):
            # Display original suggestion
            st.write("**Suggested Narrative:**")
            current_narrative = llm_result.get("suggested_narrative", "N/A")

            # Show tabs for view/edit
            tab1, tab2, tab3 = st.tabs(["📖 View", "✏️ Edit", "✅ Approve/❌ Reject"])

            with tab1:
                st.code(current_narrative)

                # Metrics
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Confidence", f"{llm_result.get('confidence_score', 0):.1%}")
                with col2:
                    st.metric("Format", llm_result.get("format_type", "N/A"))

                # Show if edited
                if was_edited:
                    st.info("✏️ This suggestion has been edited")
                    if "original_narrative" in llm_result:
                        with st.expander("See original suggestion"):
                            st.code(llm_result["original_narrative"])
                    if "edit_notes" in llm_result and llm_result["edit_notes"]:
                        st.write(f"**Edit notes:** {llm_result['edit_notes']}")

            with tab2:
                st.write("Edit the suggested narrative before approval:")
                with st.form(f"edit_form_{change_id}"):
                    edited_text = st.text_area(
                        "Narrative",
                        value=current_narrative,
                        height=150,
                        key=f"edit_narrative_{change_id}",
                    )
                    edit_notes = st.text_input(
                        "Why are you editing? (optional)",
                        placeholder="e.g., Better wording, Clarification...",
                        key=f"edit_notes_{change_id}",
                    )

                    col1, col2 = st.columns(2)
                    with col1:
                        submit_edit = st.form_submit_button("💾 Save Edit", use_container_width=True)
                    with col2:
                        st.form_submit_button("Cancel", use_container_width=True)

                    if submit_edit:
                        if edited_text.strip():
                            with st.spinner("Saving edit..."):
                                success, result = api_call(
                                    "POST",
                                    f"/changes/{change_id}/edit-suggestion",
                                    json_data={
                                        "edited_narrative": edited_text,
                                        "edit_notes": edit_notes,
                                    },
                                )

                            if success:
                                st.success("✅ Suggestion updated!")
                                st.rerun()
                            else:
                                st.error(f"Edit failed: {result}")
                        else:
                            st.error("Narrative cannot be empty")

            with tab3:
                st.write(f"**Current Narrative (to be applied to master):**")
                st.info(current_narrative)

                st.divider()

                # Approval/Rejection actions
                col1, col2 = st.columns(2)

                with col1:
                    st.write("**✅ Accept & Approve**")
                    with st.form(f"approve_form_{change_id}"):
                        comment = st.text_area(
                            "Approval comment (optional)",
                            placeholder="Add approval comment...",
                            height=80,
                            key=f"approve_comment_{change_id}",
                        )
                        st.caption("This will approve the change for application to master document")
                        submit = st.form_submit_button("✅ Approve Change", use_container_width=True, type="primary")

                        if submit:
                            if st.checkbox("I confirm this change is ready", key=f"confirm_approve_{change_id}"):
                                with st.spinner("Approving change..."):
                                    success, result = api_call(
                                        "POST",
                                        f"/changes/{change_id}/approve",
                                        json_data={"user": "dashboard_user", "comment": comment},
                                    )

                                if success:
                                    st.success("✅ Change approved and ready to apply!")
                                    st.rerun()
                                else:
                                    st.error(f"Approval failed: {result}")

                with col2:
                    st.write("**❌ Reject**")
                    with st.form(f"reject_form_{change_id}"):
                        reason = st.text_area(
                            "Rejection reason (optional)",
                            placeholder="Explain why this change is being rejected...",
                            height=80,
                            key=f"reject_reason_{change_id}",
                        )
                        st.caption("This will reject the change and mark it as not approved")
                        submit = st.form_submit_button("❌ Reject Change", use_container_width=True)

                        if submit:
                            if st.checkbox("I confirm rejection", key=f"confirm_reject_{change_id}"):
                                with st.spinner("Rejecting change..."):
                                    success, result = api_call(
                                        "POST",
                                        f"/changes/{change_id}/reject",
                                        json_data={"reason": reason or "Rejected by user"},
                                    )

                                if success:
                                    st.success("✅ Change rejected!")
                                    st.rerun()
                                else:
                                    st.error(f"Rejection failed: {result}")


# ============================================================================
# PAGE 5: MASTER DOCUMENT
# ============================================================================


def page_master_document():
    """Manage master document and apply approved changes."""
    st.title("📄 Master Document")

    # Tabs for different operations
    tab1, tab2, tab3 = st.tabs(["📤 Upload Master", "📥 Download & Info", "🚀 Apply Changes"])

    with tab1:
        st.subheader("Upload Master Credit Policy Document")
        st.write("Replace the current master policy document with a new version.")

        uploaded_file = st.file_uploader("Choose master document", type=["docx"])

        if uploaded_file:
            st.info(f"Selected: {uploaded_file.name} ({uploaded_file.size} bytes)")

            if st.button("📤 Upload Master Document", type="primary"):
                if st.checkbox("I confirm this will replace the current master document (backed up automatically)"):
                    with st.spinner("Uploading master document..."):
                        success, result = api_call(
                            "POST",
                            "/upload-master",
                            files={"file": (uploaded_file.name, uploaded_file, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
                        )

                    if success:
                        st.success("✅ Master document uploaded successfully!")
                        st.write(f"**File:** {result.get('filename')}")
                        st.write(f"**Size:** {result.get('size', 0) / 1024:.1f} KB")

                        if result.get('backup_path'):
                            st.info(f"Previous version backed up to: {result['backup_path']}")

                        st.rerun()
                    else:
                        st.error(f"Upload failed: {result}")

    with tab2:
        st.subheader("Current Master Document")

        col1, col2 = st.columns(2)

        with col1:
            st.metric("Status", "Ready")
            if st.button("📥 Download Current", type="primary", key="download_master"):
                with st.spinner("Preparing download..."):
                    st.info("Download feature: Use API endpoint /api/master/current")
                    st.code("curl http://localhost:8000/api/master/current > master.docx")

        with col2:
            st.metric("Location", "data/master_policy.docx")
            st.write("**Info:**")
            st.write("• Main policy document")
            st.write("• Auto-backed up on update")
            st.write("• Versioned after changes")

    with tab3:
        st.subheader("Apply Approved Changes")
        st.write("Apply all approved changes to the master document.")

        # Show pending approved changes
        with st.spinner("Loading approved changes..."):
            success, data = api_call("GET", "/changes/pending")

        if success:
            pending_changes = data.get("changes", [])
            approved = [c for c in pending_changes if c.get("status") == "APPROVED"]

            st.metric("Approved Changes Ready", len(approved))

            if approved:
                st.write("**Changes to be applied:**")
                for change in approved:
                    st.write(f"  • {change.get('original_data', {}).get('Section_Name', 'Unknown')}")

                if st.button("🚀 Apply All Approved Changes", type="primary"):
                    if st.checkbox("I confirm to apply all approved changes to the master document"):
                        with st.spinner("Applying changes..."):
                            success, result = api_call("POST", "/master/apply-changes")

                        if success:
                            st.success("✅ Changes applied successfully!")

                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric(
                                    "Version Created",
                                    result.get("version_created", "N/A").split("/")[-1] if result.get("version_created") else "N/A",
                                )

                            with col2:
                                st.metric("Changes Applied", result.get("changes_applied", 0))

                            st.info(
                                f"Total approved changes: {result.get('total_approved', 0)}"
                            )
                        else:
                            st.error(f"Failed to apply changes: {result}")
            else:
                st.info("No approved changes waiting to be applied.")


# ============================================================================
# PAGE 6: VERSION HISTORY
# ============================================================================


def page_version_history():
    """View version history of master document."""
    st.title("📚 Version History")

    with st.spinner("Loading version history..."):
        success, data = api_call("GET", "/master/versions")

    if not success:
        st.error(f"Failed to load versions: {data}")
        return

    versions = data.get("versions", [])
    st.metric("Total Versions", len(versions))

    if versions:
        versions_list = []
        for v in versions:
            versions_list.append({
                "Version": v.get("version", "N/A"),
                "Created": v.get("created_at", "N/A")[:10],
                "Changes Applied": v.get("changes_applied", 0),
                "Path": v.get("path", "N/A").split("/")[-1] if v.get("path") else "N/A",
            })

        df = pd.DataFrame(versions_list)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No versions found.")


# ============================================================================
# PAGE 7: LOGS
# ============================================================================


def page_logs():
    """View changes and approvals logs."""
    st.title("📋 Logs")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Changes Log")
        with st.spinner("Loading changes log..."):
            success, data = api_call("GET", "/logs/changes")

        if success:
            entries = data.get("entries", [])
            if entries:
                changes_list = []
                for entry in entries[:50]:  # Show last 50
                    changes_list.append({
                        "Timestamp": entry.get("timestamp", "N/A")[:19],
                        "Type": entry.get("type", "N/A"),
                        "Details": entry.get("details", "N/A")[:50],
                    })

                if changes_list:
                    df = pd.DataFrame(changes_list)
                    st.dataframe(df, use_container_width=True, hide_index=True)
                else:
                    st.info("No changes log entries.")
            else:
                st.info("No changes log entries.")
        else:
            st.error(f"Failed to load changes log: {data}")

    with col2:
        st.subheader("Approvals Log")
        with st.spinner("Loading approvals log..."):
            success, data = api_call("GET", "/logs/approvals")

        if success:
            entries = data.get("entries", [])
            if entries:
                approvals_list = []
                for entry in entries[:50]:  # Show last 50
                    approvals_list.append({
                        "Timestamp": entry.get("timestamp", "N/A")[:19],
                        "Change ID": entry.get("change_id", "N/A")[:20],
                        "Action": entry.get("action", "N/A"),
                        "User": entry.get("approver", "N/A")[:20],
                    })

                if approvals_list:
                    df = pd.DataFrame(approvals_list)
                    st.dataframe(df, use_container_width=True, hide_index=True)
                else:
                    st.info("No approvals log entries.")
            else:
                st.info("No approvals log entries.")
        else:
            st.error(f"Failed to load approvals log: {data}")


# ============================================================================
# UNIFIED REVIEW PAGE (3-Pane Interface)
# ============================================================================


def page_unified_review():
    """
    Unified review interface with three panes:
    Left: Master document and files
    Center: Detected changes with suggestions
    Right: Redline review (proposed changes)
    """
    st.title("📋 Policy Review - Unified Interface")

    # Create three columns
    col_left, col_center, col_right = st.columns([1, 1.5, 1.5], gap="large")

    # ============================================================================
    # LEFT PANE: MASTER FILES
    # ============================================================================
    with col_left:
        st.subheader("📄 Master Files")

        with st.container(border=True):
            st.write("**Current Master Document**")

            # Check if master exists via API
            success, master_data = api_call("GET", "/master/current-status")

            if success and master_data.get("exists"):
                file_size = master_data.get("size", 0) / (1024 * 1024)
                st.success(f"✅ Loaded: master_policy.docx")
                st.caption(f"Size: {file_size:.2f} MB")

                if st.button("📥 Download Master", key="download_master_left"):
                    success, download_data = api_call("GET", "/master/current")
                    if success:
                        st.download_button(
                            label="Download Master Document",
                            data=download_data,
                            file_name="master_policy.docx"
                        )
                    else:
                        st.error("Could not download master document")
            else:
                st.warning("⚠️ No master document uploaded yet")
                st.write("Upload a master document to begin:")

                uploaded_file = st.file_uploader(
                    "Choose Master Document",
                    type=["docx"],
                    key="upload_master_left"
                )

                if uploaded_file:
                    if st.button("⬆️ Upload Master", key="upload_master_btn_left"):
                        with st.spinner("Uploading master document..."):
                            # Call API endpoint for proper handling
                            file_bytes = uploaded_file.getvalue()
                            files = {"file": ("master_policy.docx", file_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
                            success, response = api_call("POST", "/upload-master", files=files)

                            if success:
                                saved_path = response.get("saved_to", "master_policy.docx")
                                st.success(f"✅ Master document uploaded! Saved to: {saved_path}")
                                st.rerun()
                            else:
                                st.error(f"Upload failed: {response}")

        st.divider()

        with st.container(border=True):
            st.write("**Upload Technical Document**")
            st.write("(Excel with highlighted changes)")

            uploaded_excel = st.file_uploader(
                "Choose Excel File",
                type=["xlsx"],
                key="upload_excel_left"
            )

            if uploaded_excel:
                st.info(f"📄 {uploaded_excel.name}")
                if st.button("🔍 Analyze Changes", key="analyze_left"):
                    with st.spinner("Analyzing changes..."):
                        # Upload via API
                        file_bytes = uploaded_excel.getvalue()
                        files = {"file": (uploaded_excel.name, file_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
                        success, response = api_call("POST", "/upload-excel", files=files)

                        if success:
                            total_changes = response.get("total_changes", 0)
                            st.success(f"✅ Detected {total_changes} changes!")
                            st.rerun()
                        else:
                            st.error(f"Upload failed: {response}")

    # ============================================================================
    # CENTER PANE: DETECTED CHANGES
    # ============================================================================
    with col_center:
        st.subheader("🔍 Detected Changes")

        # Get pending changes
        success, changes_data = api_call("GET", "/changes/pending")

        if not success or not changes_data.get("changes"):
            with st.container(border=True):
                st.info("📭 No changes detected yet. Upload an Excel file with highlighted cells to get started.")
        else:
            changes = changes_data.get("changes", [])

            for idx, change in enumerate(changes):
                with st.container(border=True):
                    change_type = change.get("Change_Type", "OTHER")
                    change_id = change.get("change_id", f"Change_{idx}")

                    # Color indicator
                    if change_type == "NEW":
                        color_indicator = "🟢"
                    elif change_type == "MODIFIED":
                        color_indicator = "🟡"
                    elif change_type == "DELETED":
                        color_indicator = "🔴"
                    elif change_type == "CHANGE":
                        color_indicator = "🔵"
                    else:
                        color_indicator = "⚪"

                    # Display header
                    col_header1, col_header2 = st.columns([2, 1])
                    with col_header1:
                        st.write(f"**{color_indicator} {change_type}** - {change_id}")

                    # If type is CHANGE, let user select the actual type
                    if change_type == "CHANGE":
                        with col_header2:
                            selected_type = st.selectbox(
                                "Type",
                                ["NEW", "MODIFIED", "DELETED"],
                                key=f"type_selector_{idx}",
                                label_visibility="collapsed"
                            )
                            if selected_type:
                                change["Change_Type"] = selected_type
                                change_type = selected_type

                    # Change content
                    content = change.get("Policy_Content", "")
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
                                "comment": "Accepted from unified review",
                                "change_type": change_type
                            })
                            if success:
                                st.success("✅ Accepted!")
                                st.rerun()
                    with col2:
                        if st.button("✏️ Edit", key=f"edit_{idx}", use_container_width=True):
                            st.session_state[f"editing_{idx}"] = True
                    with col3:
                        if st.button("❌ Reject", key=f"reject_{idx}", use_container_width=True):
                            success, _ = api_call("POST", f"/changes/{change_id}/reject", {
                                "reason": "Rejected from unified review"
                            })
                            if success:
                                st.error("❌ Rejected!")
                                st.rerun()

                    # Edit mode
                    if st.session_state.get(f"editing_{idx}"):
                        new_content = st.text_area(
                            "Edit content:",
                            value=content,
                            key=f"edit_content_{idx}",
                            height=100
                        )
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("💾 Save Edit", key=f"save_edit_{idx}", use_container_width=True):
                                success, _ = api_call("POST", f"/changes/{change_id}/edit-suggestion", {
                                    "edited_narrative": new_content,
                                    "edit_notes": "Edited from unified review"
                                })
                                if success:
                                    st.success("✅ Saved!")
                                    st.session_state[f"editing_{idx}"] = False
                                    st.rerun()
                        with col2:
                            if st.button("Cancel", key=f"cancel_edit_{idx}", use_container_width=True):
                                st.session_state[f"editing_{idx}"] = False

    # ============================================================================
    # RIGHT PANE: REDLINE REVIEW
    # ============================================================================
    with col_right:
        st.subheader("📝 Redline Review")

        with st.container(border=True):
            st.write("**Preview of Updated Document**")
            st.info("Shows how the master document will look after applying approved changes")

            # Get statistics
            success, changes_data = api_call("GET", "/changes/pending")
            all_changes = changes_data.get("changes", []) if success else []

            approved_count = sum(1 for c in all_changes if c.get("status") == "APPROVED")
            pending_count = sum(1 for c in all_changes if c.get("status") == "PENDING")
            rejected_count = sum(1 for c in all_changes if c.get("status") == "REJECTED")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("✅ Approved", approved_count)
            with col2:
                st.metric("⏳ Pending", pending_count)
            with col3:
                st.metric("❌ Rejected", rejected_count)

            st.divider()

            # Document preview
            st.write("**Approved Changes Summary**")
            if approved_count > 0:
                approved = [c for c in all_changes if c.get("status") == "APPROVED"]
                for c in approved:
                    st.write(f"- {c.get('Change_Type')}: {c.get('Policy_Content', '')[:50]}...")
            else:
                st.caption("No approved changes yet")

            st.divider()

            # Action buttons
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Apply All Approved", use_container_width=True):
                    with st.spinner("Applying changes..."):
                        success, result = api_call("POST", "/master/apply-changes")
                        if success:
                            st.success("✅ Changes applied to master document!")
                            st.rerun()
                        else:
                            st.error(f"Error: {result}")
            with col2:
                if st.button("📥 Download Updated", use_container_width=True):
                    success, file_data = api_call("GET", "/master/current", is_file=True)
                    if success:
                        st.download_button(
                            "Download",
                            data=file_data,
                            file_name="master_policy_updated.docx"
                        )

# ============================================================================
# SETTINGS PAGE
# ============================================================================


def page_settings():
    """Settings and configuration management."""
    st.title("⚙️ Settings")

    st.markdown("Configure your application preferences and LLM settings.")

    tab1, tab2, tab3 = st.tabs(["🔑 API Keys", "🤖 LLM Provider", "📁 File Limits"])

    # Tab 1: API Key Management
    with tab1:
        st.subheader("API Key Configuration")
        st.write("Securely manage your API keys for LLM providers.")

        from config import config

        current_provider = config.llm_provider
        has_api_key = bool(config.api_key)

        st.write(f"**Current Provider:** {current_provider.capitalize()}")
        if has_api_key:
            st.success("✅ API Key is configured")
        else:
            st.warning("⚠️ API Key is not configured (using mock provider)")

        st.divider()

        col1, col2 = st.columns(2)

        with col1:
            st.write("**Update API Key:**")
            provider = st.selectbox(
                "Select provider",
                ["anthropic", "openai", "mock"],
                index=["anthropic", "openai", "mock"].index(current_provider) if current_provider in ["anthropic", "openai", "mock"] else 0,
            )

            api_key = st.text_input(
                "API Key",
                type="password",
                placeholder="Enter your API key here",
                help="Your API key is stored securely in .env file",
            )

            if api_key:
                st.info("💾 To save this API key, manually update your .env file:")
                st.code(f"LLM_PROVIDER={provider}\nLLM_API_KEY={api_key}")
                st.caption("After updating .env, restart the application for changes to take effect")

        with col2:
            st.write("**Provider Information:**")
            if provider == "anthropic":
                st.markdown("""
                **Anthropic Claude**
                - Best quality responses
                - Recommended for production
                - Get key: https://console.anthropic.com
                """)
            elif provider == "openai":
                st.markdown("""
                **OpenAI GPT**
                - Widely available
                - Good quality responses
                - Get key: https://platform.openai.com/account/api-keys
                """)
            else:
                st.markdown("""
                **Mock Provider**
                - No API key needed
                - Perfect for testing
                - Generates sample responses
                """)

    # Tab 2: LLM Provider Settings
    with tab2:
        st.subheader("LLM Provider Configuration")
        st.write("Configure which LLM provider to use and model selection.")

        col1, col2 = st.columns(2)

        with col1:
            st.info(f"**Active Provider:** {config.llm_provider.capitalize()}")
            st.write(f"**Model:** {config.model}")
            st.write(f"**Max Tokens:** {config.max_tokens}")

        with col2:
            st.markdown("""
            **Switching Providers:**
            1. Edit your `.env` file
            2. Change `LLM_PROVIDER` to desired provider
            3. Add corresponding `LLM_API_KEY` if needed
            4. Restart the application

            **Provider Models:**
            - Anthropic: claude-3-5-sonnet-20241022, claude-3-opus-20240229
            - OpenAI: gpt-4-turbo, gpt-4, gpt-3.5-turbo
            - Mock: No configuration needed
            """)

        st.divider()
        st.caption("📖 See LLM_PROVIDERS.md in docs for detailed configuration options")

    # Tab 3: File Upload Settings
    with tab3:
        st.subheader("File Upload Configuration")
        st.write("Configure file size limits and allowed file types.")

        col1, col2 = st.columns(2)

        with col1:
            st.write("**Current Settings:**")
            st.info("""
            📊 **Max Upload Size:** Check your .env file
            📁 **Allowed Types:** .xlsx, .docx
            """)

        with col2:
            st.write("**Recommended Limits:**")
            st.markdown("""
            | Type | Recommended | Max |
            |------|-------------|-----|
            | Excel Files | ≤ 50 MB | 100 MB |
            | Word Docs | ≤ 100 MB | 500 MB |
            | Total | ≤ 150 MB | 1 GB |

            To increase limits, edit your `.env`:
            ```
            MAX_UPLOAD_SIZE=524288000  # 500 MB
            ```
            """)

    st.divider()
    st.caption("💡 Tip: Configuration changes require application restart to take effect")


# ============================================================================
# SIDEBAR CONFIGURATION
# ============================================================================


def sidebar_config():
    """Display configuration info in sidebar."""
    st.sidebar.title("⚙️ Configuration")

    with st.sidebar.expander("Backend Configuration"):
        st.write(f"**API Base URL:** {API_BASE_URL}")

        # Quick health check
        success, _ = api_call("GET", "/health")
        status_text = "✅ Online" if success else "❌ Offline"
        st.write(f"**Backend Status:** {status_text}")

    with st.sidebar.expander("Storage"):
        st.write("**File Storage:** JSON files")
        st.write("**Location:** data/ folder")
        st.write("**Change Files:** data/changes/")
        st.write("**Metadata:** data/metadata/")

    with st.sidebar.expander("LLM Configuration"):
        from config import config

        st.write(f"**Provider:** {config.llm_provider.capitalize()}")
        st.write(f"**Model:** {config.model}")
        st.write(f"**Max Tokens:** {config.max_tokens}")

        if config.api_key:
            st.write("**API Key:** ✅ Configured")
        else:
            st.warning("**API Key:** ⚠️ Not configured (using mock provider)")

        st.write("**Caching:** Enabled")
        st.caption("📖 See LLM_PROVIDERS.md for configuration options")


# ============================================================================
# MAIN APPLICATION
# ============================================================================


def main():
    """Main application entry point."""
    # Sidebar navigation
    sidebar_config()

    st.sidebar.divider()

    pages = {
        "🏠 Home": page_dashboard,
        "📋 Unified Review": page_unified_review,
        "📤 Upload Excel": page_upload_excel,
        "🔍 Review Changes": page_review_changes,
        "✅ Approve Changes": page_approve_changes,
        "📄 Master Document": page_master_document,
        "📚 Version History": page_version_history,
        "📋 Logs": page_logs,
        "⚙️ Settings": page_settings,
    }

    selected_page = st.sidebar.radio("Navigation", list(pages.keys()))

    st.sidebar.divider()

    # Footer
    st.sidebar.caption("CreditPolicyIQ v0.1.0")

    # Display selected page
    pages[selected_page]()


if __name__ == "__main__":
    main()
