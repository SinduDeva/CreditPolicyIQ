"""Change detection module for CreditPolicyIQ."""
import logging
import hashlib
from typing import Dict, List, Any, Optional
from difflib import SequenceMatcher
from pathlib import Path

logger = logging.getLogger(__name__)


class ChangeDetector:
    """Detects and matches policy changes between Excel and master document."""

    def __init__(self):
        """Initialize change detector."""
        self.logger = logger

    def detect_changes(
        self, excel_changes: List[Dict[str, Any]], master_docx_path: str
    ) -> Dict[str, Any]:
        """
        Detect and map Excel changes to master document sections.

        Args:
            excel_changes: List of changes from Excel parser
            master_docx_path: Path to master DOCX file

        Returns:
            Dictionary with detected_changes list
        """
        if not Path(master_docx_path).exists():
            self.logger.error(f"Master DOCX not found: {master_docx_path}")
            return {"detected_changes": [], "error": "Master document not found"}

        try:
            detected_changes = []

            for change in excel_changes:
                # Generate unique change ID
                change_id = self.generate_change_id(change)

                # Find matching section in master document
                match_details = self.find_matching_section(
                    change, master_docx_path
                )

                detected_change = {
                    "change_id": change_id,
                    "original_data": change,
                    "match_details": match_details,
                    "confidence_score": match_details.get("similarity_score", 0),
                    "status": "PENDING",
                    "created_at": self._get_timestamp(),
                }

                detected_changes.append(detected_change)
                self.logger.debug(
                    f"Detected change {change_id} with confidence "
                    f"{match_details.get('similarity_score', 0):.2%}"
                )

            self.logger.info(f"Detected {len(detected_changes)} changes from Excel")
            return {"detected_changes": detected_changes}

        except Exception as e:
            self.logger.error(f"Error detecting changes: {e}")
            return {"detected_changes": [], "error": str(e)}

    def find_matching_section(
        self, excel_change: Dict[str, Any], master_docx_path: str
    ) -> Dict[str, Any]:
        """
        Find matching section in master document using fuzzy matching.

        Args:
            excel_change: Change from Excel
            master_docx_path: Path to master document

        Returns:
            Dictionary with section match details
        """
        try:
            # Import here to avoid circular dependency
            from core.docx_handler import DocxHandler

            docx_handler = DocxHandler()
            structure = docx_handler.extract_structure(master_docx_path)

            if "error" in structure:
                self.logger.warning(f"Could not extract document structure: {structure['error']}")
                return {
                    "matched": False,
                    "similarity_score": 0,
                    "section_index": None,
                    "reason": "Could not extract structure",
                }

            excel_section_name = excel_change.get("Section_Name", "").lower()
            excel_content = excel_change.get("Policy_Content", "").lower()

            best_match = None
            best_score = 0

            # Try to match by section name first
            for section_idx, section in enumerate(structure.get("sections", [])):
                section_title = section.get("title", "").lower()

                # Match on section name
                name_similarity = self._calculate_similarity(
                    excel_section_name, section_title
                )

                # Match on content in section
                section_paragraphs = section.get("paragraphs", [])
                content_similarity = 0

                for para_idx in section_paragraphs:
                    if para_idx < len(structure.get("paragraphs", [])):
                        para_text = (
                            structure["paragraphs"][para_idx].get("text", "").lower()
                        )
                        sim = self._calculate_similarity(excel_content, para_text)
                        content_similarity = max(content_similarity, sim)

                # Combined score (weight name match higher)
                combined_score = name_similarity * 0.6 + content_similarity * 0.4

                if combined_score > best_score:
                    best_score = combined_score
                    best_match = {
                        "matched": True,
                        "section_index": section_idx,
                        "section_title": section.get("title"),
                        "similarity_score": combined_score,
                        "name_similarity": name_similarity,
                        "content_similarity": content_similarity,
                        "start_para_idx": section.get("start_para_idx"),
                    }

            if best_match and best_score >= 0.3:
                return best_match
            else:
                return {
                    "matched": False,
                    "similarity_score": best_score or 0,
                    "section_index": None,
                    "reason": "No good match found",
                }

        except Exception as e:
            self.logger.error(f"Error finding matching section: {e}")
            return {
                "matched": False,
                "similarity_score": 0,
                "section_index": None,
                "reason": str(e),
            }

    def generate_change_id(self, excel_change: Dict[str, Any]) -> str:
        """
        Generate unique change ID using MD5 hash.

        Args:
            excel_change: Change dictionary

        Returns:
            Unique change ID like "CHANGE_ABC123DE"
        """
        try:
            # Combine section name and content for hash
            content = f"{excel_change.get('Section_ID', '')}_{excel_change.get('Section_Name', '')}"
            hash_obj = hashlib.md5(content.encode())
            hash_hex = hash_obj.hexdigest().upper()[:8]
            change_id = f"CHANGE_{hash_hex}"
            return change_id
        except Exception as e:
            self.logger.error(f"Error generating change ID: {e}")
            return "CHANGE_UNKNOWN"

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity between two texts using SequenceMatcher.

        Args:
            text1: First text
            text2: Second text

        Returns:
            Similarity score between 0 and 1
        """
        if not text1 or not text2:
            return 0.0
        return SequenceMatcher(None, text1, text2).ratio()

    def _get_timestamp(self) -> str:
        """
        Get current timestamp in ISO format.

        Returns:
            ISO format timestamp string
        """
        from datetime import datetime

        return datetime.utcnow().isoformat()
