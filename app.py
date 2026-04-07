"""FastAPI application for CreditPolicyIQ POC."""
import logging
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from fastapi import FastAPI, UploadFile, File, HTTPException, Body
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from config import config
from utils.logger import setup_logger
from utils.file_storage import file_storage
from core.intelligent_excel_parser import IntelligentExcelParser
from core.excel_parser import ExcelParser
from core.change_detector import ChangeDetector
from core.change_mapper import ChangeMapper
from core.docx_handler import DocxHandler
from core.llm_caller import LLMCaller
from core.approval_workflow import ApprovalWorkflow

# Initialize logger
logger = setup_logger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="CreditPolicyIQ",
    description="Credit Policy Automation POC",
    version="0.1.0",
)

# Add CORS middleware for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize core modules
# Use intelligent parser that works with any Excel structure
excel_parser = IntelligentExcelParser()
change_detector = ChangeDetector()
change_mapper = ChangeMapper()
docx_handler = DocxHandler()
approval_workflow = ApprovalWorkflow()
llm_caller = None  # Lazy initialize due to API key requirement


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    logger.info("Starting CreditPolicyIQ application")
    logger.info(f"Configuration: {config.to_dict()}")

    # Create required directories
    Path("data/changes").mkdir(parents=True, exist_ok=True)
    Path("data/metadata").mkdir(parents=True, exist_ok=True)
    Path("data/cache").mkdir(parents=True, exist_ok=True)
    Path("logs").mkdir(parents=True, exist_ok=True)

    logger.info("Application startup complete")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown."""
    logger.info("Shutting down CreditPolicyIQ application")


# ============================================================================
# UPLOAD & FILE MANAGEMENT ENDPOINTS
# ============================================================================


@app.post("/api/upload-excel")
async def upload_excel(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Upload and parse Excel file with policy changes.

    Args:
        file: Excel file (.xlsx)

    Returns:
        Upload status with parsed changes and summary
    """
    try:
        # Validate file type
        if not file.filename.endswith(".xlsx"):
            logger.warning(f"Invalid file type uploaded: {file.filename}")
            raise HTTPException(
                status_code=400, detail="File must be .xlsx format"
            )

        # Save uploaded file
        upload_dir = Path("data/uploads")
        upload_dir.mkdir(parents=True, exist_ok=True)
        file_path = upload_dir / file.filename

        contents = await file.read()
        # Validate file size (max 10MB default)
        max_size = 10 * 1024 * 1024
        if len(contents) > max_size:
            logger.warning(
                f"File too large: {file.filename} ({len(contents)} bytes)"
            )
            raise HTTPException(
                status_code=400,
                detail=f"File size exceeds {max_size / 1024 / 1024}MB limit",
            )

        with open(file_path, "wb") as f:
            f.write(contents)

        logger.info(f"File uploaded: {file.filename}")

        # Parse Excel file
        parse_result = excel_parser.parse_excel(str(file_path))

        if "error" in parse_result:
            logger.error(f"Error parsing Excel: {parse_result['error']}")
            raise HTTPException(status_code=400, detail=parse_result["error"])

        # Convert intelligent parser output to change_detector format
        parsed_changes = parse_result.get("parsed_changes", [])
        converted_changes = []

        for change in parsed_changes:
            # Extract section name from context or use default
            context = change.get("context", {})
            all_text = context.get("all_text", change.get("content", ""))

            converted_change = {
                "change_id": change.get("change_id"),
                "Section_Name": f"{change.get('type')} Change",  # Use change type as section name
                "Policy_Content": change.get("content", ""),  # Use colored cell text as content
                "Context": context.get("before", ""),  # Use before context
                "Change_Type": change.get("type"),  # NEW, MODIFIED, or DELETED
                "source": change.get("source", {}),  # Keep source info
                "original_data": change,  # Keep original for reference
            }
            converted_changes.append(converted_change)

        logger.info(f"Converted {len(converted_changes)} changes for detection")
        detection_result = change_detector.detect_changes(
            converted_changes, config.master_docx
        )

        detected_changes = detection_result.get("detected_changes", [])

        # Enhance changes with intelligent mapping information
        docx_handler = DocxHandler()
        master_structure = docx_handler.extract_structure(config.master_docx)

        enhanced_changes = []
        for change in detected_changes:
            # Get intelligent mapping for this change
            mapping_result = change_mapper.map_change_to_section(
                change.get("original_data", {}),
                master_structure
            )

            # Add mapping info to change
            change["mapping"] = mapping_result
            change["mapping_confidence"] = mapping_result.get("confidence", 0)
            change["suggested_section"] = mapping_result.get("section_title", "Unknown")

            enhanced_changes.append(change)

        detected_changes = enhanced_changes

        # Save changes to JSON files
        for change in detected_changes:
            change_id = change.get("change_id")
            file_storage.save_json(
                f"changes/{change_id}.json", change
            )
            logger.info(f"Saved change {change_id}")

        # Log upload
        file_storage.append_to_log(
            "metadata/upload_log.json",
            {
                "filename": file.filename,
                "size": len(contents),
                "total_changes": len(detected_changes),
            },
        )

        logger.info(
            f"Successfully processed {file.filename}: {len(detected_changes)} changes"
        )

        return {
            "status": "success",
            "file_uploaded": file.filename,
            "total_changes": len(detected_changes),
            "changes": detected_changes,
            "excel_summary": parse_result.get("summary", {}),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in upload_excel: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/upload-master")
async def upload_master(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Upload and replace master DOCX file.

    Args:
        file: Master document file (.docx)

    Returns:
        Upload status with document info
    """
    try:
        # Validate file type
        if not file.filename.endswith(".docx"):
            logger.warning(f"Invalid file type uploaded: {file.filename}")
            raise HTTPException(
                status_code=400, detail="File must be .docx format"
            )

        # Read file contents
        contents = await file.read()

        # Validate file size (max 50MB for documents)
        max_size = 50 * 1024 * 1024
        if len(contents) > max_size:
            logger.warning(
                f"File too large: {file.filename} ({len(contents)} bytes)"
            )
            raise HTTPException(
                status_code=400,
                detail=f"File size exceeds {max_size / 1024 / 1024}MB limit",
            )

        # Backup existing master document if it exists
        master_path = Path(config.master_docx)
        backup_path = None  # Initialize as None

        if master_path.exists():
            backup_dir = Path("data/backups")
            backup_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = backup_dir / f"master_policy_backup_{timestamp}.docx"

            import shutil
            shutil.copy2(master_path, backup_path)
            logger.info(f"Backed up existing master to {backup_path}")

        # Save new master document
        master_path.parent.mkdir(parents=True, exist_ok=True)
        with open(master_path, "wb") as f:
            f.write(contents)

        # Verify file was saved
        if not master_path.exists():
            logger.error(f"Failed to save master document to {master_path}")
            raise HTTPException(
                status_code=500, detail="Failed to save master document"
            )

        logger.info(f"Master document saved to {master_path} ({len(contents)} bytes)")

        # Extract and validate document structure
        try:
            docx_handler.extract_structure(str(master_path))
            logger.info(f"Validated master document structure")
        except Exception as e:
            logger.warning(f"Could not fully validate document: {e}")

        # Log upload
        file_storage.append_to_log(
            "metadata/master_upload_log.json",
            {
                "filename": file.filename,
                "size": len(contents),
                "action": "master_document_uploaded",
                "saved_to": str(master_path),
            },
        )

        logger.info(f"Master document uploaded: {file.filename} ({len(contents)} bytes)")

        return {
            "status": "success",
            "filename": file.filename,
            "size": len(contents),
            "message": "Master document updated successfully",
            "saved_to": str(master_path),
            "backup_path": str(backup_path) if backup_path else None,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in upload_master: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/master/current")
async def get_master_current() -> FileResponse:
    """
    Download current master DOCX file.

    Returns:
        File response with master document
    """
    try:
        master_path = Path(config.master_docx)

        if not master_path.exists():
            logger.warning(f"Master document not found: {master_path}")
            raise HTTPException(status_code=404, detail="Master document not found")

        logger.info(f"Downloading master document: {master_path}")

        return FileResponse(
            path=master_path,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename="master_policy.docx",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_master_current: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/master/versions")
async def get_master_versions() -> Dict[str, Any]:
    """
    Get list of all master document versions.

    Returns:
        List of versions with metadata
    """
    try:
        # Load version metadata
        metadata = file_storage.load_json("metadata/documents_metadata.json")

        if not metadata:
            logger.info("No version metadata found, returning empty list")
            return {"status": "success", "versions": []}

        versions = metadata.get("versions", [])
        logger.info(f"Retrieved {len(versions)} versions")

        return {
            "status": "success",
            "versions": versions,
            "total_versions": len(versions),
        }

    except Exception as e:
        logger.error(f"Error in get_master_versions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# CHANGE MANAGEMENT ENDPOINTS
# ============================================================================


@app.get("/api/changes/pending")
async def get_pending_changes() -> Dict[str, Any]:
    """
    Get all pending changes (not yet applied).

    Returns:
        List of pending changes
    """
    try:
        pending_changes = approval_workflow.get_pending_changes()
        logger.info(f"Retrieved {len(pending_changes)} pending changes")

        return {
            "status": "success",
            "total_pending": len(pending_changes),
            "changes": pending_changes,
        }

    except Exception as e:
        logger.error(f"Error in get_pending_changes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/changes/{change_id}/translate")
async def translate_change(change_id: str) -> Dict[str, Any]:
    """
    Translate a change using Claude API.

    Args:
        change_id: ID of change to translate

    Returns:
        Translation result with LLM suggestion
    """
    try:
        # Load change from file
        change_data = file_storage.load_json(f"changes/{change_id}.json")

        if not change_data:
            logger.warning(f"Change not found: {change_id}")
            raise HTTPException(status_code=404, detail=f"Change {change_id} not found")

        # Initialize LLM caller if needed
        global llm_caller
        if not llm_caller:
            # Initialize LLM caller with configured provider
            # Falls back to mock provider if API key not available
            logger.info(f"Initializing LLM caller with provider: {config.llm_provider}")
            llm_caller = LLMCaller(
                api_key=config.api_key,
                provider=config.llm_provider,
                model=config.model,
            )

            if config.api_key:
                logger.info(f"LLM provider: {config.llm_provider} with API key configured")
            else:
                logger.warning(
                    "No LLM API key configured. Using mock provider for testing. "
                    "Set LLM_API_KEY environment variable to enable real LLM features."
                )

        logger.info(f"Translating change {change_id}")

        # Get document context
        match_details = change_data.get("match_details", {})
        context = f"Section: {match_details.get('section_title', 'Unknown')}"

        # Call LLM
        llm_result = llm_caller.translate_change(
            change_data, context, config.master_docx
        )

        # Update change with LLM suggestion
        change_data["status"] = "PENDING_REVIEW"
        change_data["llm_suggestion"] = llm_result
        change_data["translated_at"] = datetime.utcnow().isoformat()

        # Save updated change
        file_storage.save_json(f"changes/{change_id}.json", change_data)

        # Log translation
        file_storage.append_to_log(
            "metadata/translation_log.json",
            {
                "change_id": change_id,
                "status": "translated",
                "confidence": llm_result.get("confidence_score", 0),
            },
        )

        logger.info(f"Successfully translated change {change_id}")

        return {
            "status": "success",
            "change_id": change_id,
            "suggestion": llm_result,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in translate_change: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/changes/{change_id}/edit-suggestion")
async def edit_suggestion(
    change_id: str, body: Dict[str, str] = Body(...)
) -> Dict[str, Any]:
    """
    Edit the LLM-suggested narrative for a change.

    Args:
        change_id: ID of change to edit
        body: JSON body with edited_narrative and optional notes

    Returns:
        Updated change with edited suggestion
    """
    try:
        edited_narrative = body.get("edited_narrative", "")
        edit_notes = body.get("edit_notes", "")

        # Load change from file
        change_data = file_storage.load_json(f"changes/{change_id}.json")

        if not change_data:
            logger.warning(f"Change not found: {change_id}")
            raise HTTPException(
                status_code=404, detail=f"Change {change_id} not found"
            )

        # Validate edited narrative is not empty
        if not edited_narrative.strip():
            logger.warning(f"Empty narrative provided for change {change_id}")
            raise HTTPException(
                status_code=400, detail="Narrative cannot be empty"
            )

        # Update the suggested narrative
        if "llm_suggestion" not in change_data:
            change_data["llm_suggestion"] = {}

        original_narrative = change_data["llm_suggestion"].get("suggested_narrative", "")
        change_data["llm_suggestion"]["suggested_narrative"] = edited_narrative
        change_data["llm_suggestion"]["was_edited"] = True
        change_data["llm_suggestion"]["original_narrative"] = original_narrative
        change_data["llm_suggestion"]["edit_notes"] = edit_notes
        change_data["llm_suggestion"]["edited_at"] = datetime.utcnow().isoformat()

        # Save updated change
        file_storage.save_json(f"changes/{change_id}.json", change_data)

        # Log edit
        file_storage.append_to_log(
            "metadata/edit_log.json",
            {
                "change_id": change_id,
                "action": "suggestion_edited",
                "notes": edit_notes,
            },
        )

        logger.info(f"Edited suggestion for change {change_id}")

        return {
            "status": "success",
            "change_id": change_id,
            "message": "Suggestion updated. You can now approve the change.",
            "edited_narrative": edited_narrative,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in edit_suggestion: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/changes/{change_id}/approve")
async def approve_change(
    change_id: str, body: Dict[str, str] = Body(...)
) -> Dict[str, Any]:
    """
    Approve a change.

    Args:
        change_id: ID of change to approve
        body: JSON body with user and comment

    Returns:
        Approval status
    """
    try:
        user = body.get("user", "unknown")
        comment = body.get("comment", "")

        # Approve change
        success = approval_workflow.approve_change(change_id, user, comment)

        if not success:
            logger.warning(f"Failed to approve change {change_id}")
            raise HTTPException(
                status_code=404, detail=f"Change {change_id} not found"
            )

        # Log approval
        file_storage.append_to_log(
            "metadata/approvals_log.json",
            {
                "change_id": change_id,
                "approver": user,
                "action": "APPROVED",
                "comment": comment,
            },
        )

        logger.info(f"Approved change {change_id} by {user}")

        return {
            "status": "success",
            "change_id": change_id,
            "new_status": "APPROVED",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in approve_change: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/changes/{change_id}/reject")
async def reject_change(
    change_id: str, body: Dict[str, str] = Body(...)
) -> Dict[str, Any]:
    """
    Reject a change.

    Args:
        change_id: ID of change to reject
        body: JSON body with reason

    Returns:
        Rejection status
    """
    try:
        reason = body.get("reason", "No reason provided")

        # Reject change
        success = approval_workflow.reject_change(change_id, reason)

        if not success:
            logger.warning(f"Failed to reject change {change_id}")
            raise HTTPException(
                status_code=404, detail=f"Change {change_id} not found"
            )

        # Log rejection
        file_storage.append_to_log(
            "metadata/approvals_log.json",
            {
                "change_id": change_id,
                "action": "REJECTED",
                "reason": reason,
            },
        )

        logger.info(f"Rejected change {change_id}: {reason}")

        return {
            "status": "success",
            "change_id": change_id,
            "new_status": "REJECTED",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in reject_change: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# APPLY CHANGES ENDPOINT
# ============================================================================


@app.post("/api/master/apply-changes")
async def apply_changes() -> Dict[str, Any]:
    """
    Apply all approved changes to master document and create new version.

    Returns:
        Application status with version info
    """
    try:
        logger.info("Starting application of approved changes")

        # Get all approved changes
        pending_changes = approval_workflow.get_pending_changes()
        approved_changes = [
            c for c in pending_changes if c.get("status") == "APPROVED"
        ]

        if not approved_changes:
            logger.info("No approved changes to apply")
            return {
                "status": "success",
                "version_created": None,
                "changes_applied": 0,
                "total_approved": 0,
            }

        # Create new version
        version_path = approval_workflow.create_new_version()

        if not version_path:
            logger.error("Failed to create new version")
            raise HTTPException(
                status_code=500, detail="Failed to create new version"
            )

        # Apply changes
        apply_result = approval_workflow.apply_changes()

        # Update metadata
        metadata = file_storage.load_json("metadata/documents_metadata.json") or {
            "versions": []
        }

        version_info = {
            "version": apply_result.get("applied_count", 0),
            "created_at": datetime.utcnow().isoformat(),
            "changes_applied": apply_result.get("applied_count", 0),
            "path": version_path,
        }

        if "versions" not in metadata:
            metadata["versions"] = []

        metadata["versions"].append(version_info)
        metadata["current_version"] = version_path

        file_storage.save_json("metadata/documents_metadata.json", metadata)

        # Log application
        file_storage.append_to_log(
            "metadata/application_log.json",
            {
                "version": version_path,
                "changes_applied": apply_result.get("applied_count", 0),
                "total_approved": apply_result.get("total_approved", 0),
            },
        )

        logger.info(
            f"Applied {apply_result.get('applied_count', 0)} changes, "
            f"version {version_path} created"
        )

        return {
            "status": "success",
            "version_created": version_path,
            "changes_applied": apply_result.get("applied_count", 0),
            "total_approved": apply_result.get("total_approved", 0),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in apply_changes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# LOGS ENDPOINTS
# ============================================================================


@app.get("/api/logs/changes")
async def get_changes_log() -> Dict[str, Any]:
    """
    Get changes log.

    Returns:
        All changes log entries
    """
    try:
        log_data = file_storage.load_json("metadata/changes_log.json") or {
            "entries": []
        }
        entries = log_data.get("entries", [])

        logger.info(f"Retrieved {len(entries)} change log entries")

        return {
            "status": "success",
            "total_entries": len(entries),
            "entries": entries,
        }

    except Exception as e:
        logger.error(f"Error in get_changes_log: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/logs/approvals")
async def get_approvals_log() -> Dict[str, Any]:
    """
    Get approvals log.

    Returns:
        All approval log entries
    """
    try:
        log_data = file_storage.load_json("metadata/approvals_log.json") or {
            "entries": []
        }
        entries = log_data.get("entries", [])

        logger.info(f"Retrieved {len(entries)} approval log entries")

        return {
            "status": "success",
            "total_entries": len(entries),
            "entries": entries,
        }

    except Exception as e:
        logger.error(f"Error in get_approvals_log: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# HEALTH CHECK
# ============================================================================


@app.get("/api/health")
async def health_check() -> Dict[str, str]:
    """
    Health check endpoint.

    Returns:
        Health status
    """
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
