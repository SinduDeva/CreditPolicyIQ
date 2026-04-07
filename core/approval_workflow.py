"""Approval workflow module for CreditPolicyIQ."""
import logging
import json
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime
from config import config

logger = logging.getLogger(__name__)

# Change status constants
STATUS_PENDING = "PENDING"
STATUS_APPROVED = "APPROVED"
STATUS_REJECTED = "REJECTED"
STATUS_APPLIED = "APPLIED"


class ApprovalWorkflow:
    """Manages approval workflow for policy changes."""

    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize approval workflow.

        Args:
            data_dir: Base data directory (uses config if not provided)
        """
        self.data_dir = Path(data_dir or config.data_dir)
        self.changes_dir = self.data_dir / "changes"
        self.changes_dir.mkdir(parents=True, exist_ok=True)
        self.approval_log_path = self.data_dir / "approval_log.json"
        self.logger = logger

    def get_pending_changes(self) -> List[Dict[str, Any]]:
        """
        Get all pending changes from data directory.

        Returns:
            List of pending change dictionaries
        """
        try:
            pending_changes = []

            if not self.changes_dir.exists():
                self.logger.warning(f"Changes directory not found: {self.changes_dir}")
                return []

            # Scan for JSON files in changes directory
            for change_file in self.changes_dir.glob("*.json"):
                try:
                    with open(change_file, "r") as f:
                        change = json.load(f)
                        if change.get("status") == STATUS_PENDING:
                            pending_changes.append(change)
                except Exception as e:
                    self.logger.warning(
                        f"Error reading change file {change_file}: {e}"
                    )

            self.logger.info(f"Found {len(pending_changes)} pending changes")
            return pending_changes

        except Exception as e:
            self.logger.error(f"Error getting pending changes: {e}")
            return []

    def approve_change(
        self, change_id: str, approver: str, comment: str = "", change_type: Optional[str] = None
    ) -> bool:
        """
        Approve a change and update its status.

        Args:
            change_id: ID of change to approve
            approver: Name/ID of approver
            comment: Approval comment
            change_type: Optional change type to set (NEW, MODIFIED, DELETED, CHANGE)

        Returns:
            True if successful, False otherwise
        """
        try:
            change_file = self.changes_dir / f"{change_id}.json"

            if not change_file.exists():
                self.logger.error(f"Change file not found: {change_file}")
                return False

            with open(change_file, "r") as f:
                change = json.load(f)

            # Update change status
            change["status"] = STATUS_APPROVED
            change["approved_by"] = approver
            change["approved_at"] = datetime.utcnow().isoformat()
            change["approval_comment"] = comment

            # Update change type if provided (e.g., user selected from dropdown)
            if change_type and change_type in ["NEW", "MODIFIED", "DELETED"]:
                change["Change_Type"] = change_type
                self.logger.info(f"Set change {change_id} type to {change_type}")

            # Save updated change
            with open(change_file, "w") as f:
                json.dump(change, f, indent=2)

            # Log approval
            self._log_approval(change_id, approver, "APPROVED", comment)

            self.logger.info(f"Approved change {change_id} by {approver} (type: {change.get('Change_Type')})")
            return True

        except Exception as e:
            self.logger.error(f"Error approving change {change_id}: {e}")
            return False

    def reject_change(self, change_id: str, reason: str) -> bool:
        """
        Reject a change and update its status.

        Args:
            change_id: ID of change to reject
            reason: Reason for rejection

        Returns:
            True if successful, False otherwise
        """
        try:
            change_file = self.changes_dir / f"{change_id}.json"

            if not change_file.exists():
                self.logger.error(f"Change file not found: {change_file}")
                return False

            with open(change_file, "r") as f:
                change = json.load(f)

            # Update change status
            change["status"] = STATUS_REJECTED
            change["rejection_reason"] = reason
            change["rejected_at"] = datetime.utcnow().isoformat()

            # Save updated change
            with open(change_file, "w") as f:
                json.dump(change, f, indent=2)

            # Log rejection
            self._log_approval(change_id, "System", "REJECTED", reason)

            self.logger.info(f"Rejected change {change_id}: {reason}")
            return True

        except Exception as e:
            self.logger.error(f"Error rejecting change {change_id}: {e}")
            return False

    def apply_changes(self, change_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Apply all approved changes to master document.

        Args:
            change_ids: Optional list of specific change IDs to apply (uses all approved if None)

        Returns:
            Dictionary with applied_changes count and errors
        """
        try:
            from core.docx_handler import DocxHandler

            # Get approved changes
            if change_ids:
                changes_to_apply = []
                for change_id in change_ids:
                    change_file = self.changes_dir / f"{change_id}.json"
                    if change_file.exists():
                        with open(change_file, "r") as f:
                            change = json.load(f)
                            if change.get("status") == STATUS_APPROVED:
                                changes_to_apply.append(change)
            else:
                changes_to_apply = [
                    c
                    for c in self._load_all_changes()
                    if c.get("status") == STATUS_APPROVED
                ]

            docx_handler = DocxHandler()
            applied_count = 0
            errors = []

            for change in changes_to_apply:
                try:
                    match_details = change.get("match_details", {})
                    para_index = match_details.get("start_para_idx")

                    if para_index is None:
                        errors.append(
                            {
                                "change_id": change.get("change_id"),
                                "error": "No matching paragraph found",
                            }
                        )
                        continue

                    # Extract document structure
                    docx_handler.extract_structure(config.master_docx)

                    change_type = change.get("Change_Type", "MODIFIED")
                    output_path = config.master_docx + ".updated"
                    success = False

                    if change_type == "DELETED":
                        # Delete the paragraph
                        success = docx_handler.delete_paragraph(para_index, output_path)
                        action_desc = "Delete"
                    else:
                        # Update paragraph for NEW or MODIFIED
                        new_text = change.get("suggested_narrative", "")
                        success = docx_handler.update_paragraph(
                            para_index, new_text, output_path
                        )
                        action_desc = "Update"

                    if success:
                        # Mark change as applied
                        change["status"] = STATUS_APPLIED
                        change["applied_at"] = datetime.utcnow().isoformat()

                        # Save updated change file
                        change_file = self.changes_dir / f"{change.get('change_id')}.json"
                        with open(change_file, "w") as f:
                            json.dump(change, f, indent=2)

                        applied_count += 1
                        self.logger.info(
                            f"{action_desc} change {change.get('change_id')} (type: {change_type})"
                        )
                    else:
                        errors.append(
                            {
                                "change_id": change.get("change_id"),
                                "error": f"Failed to {action_desc.lower()} paragraph",
                            }
                        )

                except Exception as e:
                    errors.append(
                        {
                            "change_id": change.get("change_id"),
                            "error": str(e),
                        }
                    )
                    self.logger.error(
                        f"Error applying change {change.get('change_id')}: {e}"
                    )

            return {
                "applied_count": applied_count,
                "total_approved": len(changes_to_apply),
                "errors": errors,
            }

        except Exception as e:
            self.logger.error(f"Error in apply_changes: {e}")
            return {
                "applied_count": 0,
                "total_approved": 0,
                "errors": [{"error": str(e)}],
            }

    def create_new_version(self) -> str:
        """
        Create new version of master document.

        Returns:
            Path to new version file
        """
        try:
            import shutil

            master_path = Path(config.master_docx)
            if not master_path.exists():
                self.logger.error(f"Master document not found: {master_path}")
                return ""

            # Get current version number
            version_info = self._get_version_info()
            new_version = version_info.get("current_version", 0) + 1

            # Create backup with version number
            backup_name = f"{master_path.stem}_v{new_version}{master_path.suffix}"
            backup_path = master_path.parent / backup_name

            shutil.copy2(master_path, backup_path)

            # Update version info
            version_info["current_version"] = new_version
            version_info["last_updated"] = datetime.utcnow().isoformat()

            version_file = self.data_dir / "version_info.json"
            with open(version_file, "w") as f:
                json.dump(version_info, f, indent=2)

            self.logger.info(f"Created version {new_version}: {backup_path}")
            return str(backup_path)

        except Exception as e:
            self.logger.error(f"Error creating new version: {e}")
            return ""

    def _load_all_changes(self) -> List[Dict[str, Any]]:
        """
        Load all changes from data directory.

        Returns:
            List of all changes
        """
        changes = []
        for change_file in self.changes_dir.glob("*.json"):
            try:
                with open(change_file, "r") as f:
                    changes.append(json.load(f))
            except Exception as e:
                self.logger.warning(f"Error loading {change_file}: {e}")
        return changes

    def _log_approval(
        self, change_id: str, approver: str, action: str, details: str = ""
    ) -> None:
        """
        Log approval action to log file.

        Args:
            change_id: Change ID
            approver: Approver identifier
            action: Action type (APPROVED, REJECTED)
            details: Additional details
        """
        try:
            # Load existing log or create new
            log_data = {}
            if self.approval_log_path.exists():
                with open(self.approval_log_path, "r") as f:
                    log_data = json.load(f)

            # Add new entry
            if "entries" not in log_data:
                log_data["entries"] = []

            log_data["entries"].append(
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "change_id": change_id,
                    "approver": approver,
                    "action": action,
                    "details": details,
                }
            )

            # Save log
            with open(self.approval_log_path, "w") as f:
                json.dump(log_data, f, indent=2)

        except Exception as e:
            self.logger.warning(f"Error logging approval: {e}")

    def _get_version_info(self) -> Dict[str, Any]:
        """
        Get version information.

        Returns:
            Version info dictionary
        """
        try:
            version_file = self.data_dir / "version_info.json"
            if version_file.exists():
                with open(version_file, "r") as f:
                    return json.load(f)
        except Exception as e:
            self.logger.warning(f"Error reading version info: {e}")
        return {"current_version": 0}
