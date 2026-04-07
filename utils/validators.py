"""Validation utilities for CreditPolicyIQ."""
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

# Minimal required columns for Excel parsing
# Only Section_Name and Policy_Content are mandatory
REQUIRED_EXCEL_COLUMNS = [
    "Section_Name",
    "Policy_Content",
]

# Optional columns that enhance functionality
OPTIONAL_EXCEL_COLUMNS = [
    "Section_ID",
    "UW_Technical_Details",
    "Status",
    "Color_Flag",
    "Notes",
]


def validate_excel_columns(columns: List[str]) -> bool:
    """
    Validate that Excel sheet contains all required columns.

    Args:
        columns: List of column names from the sheet

    Returns:
        True if all required columns present, False otherwise
    """
    missing = set(REQUIRED_EXCEL_COLUMNS) - set(columns)
    if missing:
        logger.warning(f"Missing required columns: {missing}")
        return False
    return True


def validate_change_data(change: Dict[str, Any]) -> bool:
    """
    Validate change data structure.

    Args:
        change: Change dictionary to validate

    Returns:
        True if valid, False otherwise
    """
    required_fields = ["Section_ID", "Section_Name", "Policy_Content"]
    missing = set(required_fields) - set(change.keys())
    if missing:
        logger.warning(f"Change missing fields: {missing}")
        return False
    return True


def validate_docx_path(path: str) -> bool:
    """
    Validate DOCX file path.

    Args:
        path: Path to DOCX file

    Returns:
        True if file exists and has .docx extension
    """
    import os

    if not os.path.exists(path):
        logger.warning(f"DOCX file not found: {path}")
        return False
    if not path.lower().endswith(".docx"):
        logger.warning(f"Invalid file extension: {path}")
        return False
    return True


def validate_excel_path(path: str) -> bool:
    """
    Validate Excel file path.

    Args:
        path: Path to Excel file

    Returns:
        True if file exists and has .xlsx extension
    """
    import os

    if not os.path.exists(path):
        logger.warning(f"Excel file not found: {path}")
        return False
    if not path.lower().endswith(".xlsx"):
        logger.warning(f"Invalid file extension: {path}")
        return False
    return True
