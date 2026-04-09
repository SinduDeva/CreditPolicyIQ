"""Generate and manage document previews for change visualization."""
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
from docx import Document

from core.table_extractor import TableExtractor
from core.docx_handler import DocxHandler
from core.html_converter import HTMLConverter

logger = logging.getLogger(__name__)


class DocumentPreview:
    """Generate previews of Word documents with change highlighting."""

    def __init__(self):
        """Initialize document preview generator."""
        self.logger = logger
        self.table_extractor = TableExtractor()
        self.docx_handler = DocxHandler()
        self.html_converter = HTMLConverter()
        self._cached_structure = None
        self._cached_html = None

    def load_document(self, docx_path: str) -> bool:
        """
        Load and cache document structure.

        Args:
            docx_path: Path to master .docx file

        Returns:
            True if successful, False otherwise
        """
        try:
            if not Path(docx_path).exists():
                self.logger.error(f"Document not found: {docx_path}")
                return False

            # Extract document structure
            self._cached_structure = self.docx_handler.extract_structure(docx_path)
            if not self._cached_structure:
                return False

            # Extract all tables for complete structure
            doc = Document(docx_path)
            tables = self.table_extractor.extract_all_tables(docx_path)

            # Merge tables into document structure for complete context
            self._cached_structure["tables"] = tables

            self.logger.info(f"Loaded document: {docx_path}")
            self._cached_html = None  # Invalidate cached HTML
            return True

        except Exception as e:
            self.logger.error(f"Error loading document: {e}")
            return False

    def get_full_document_html(self) -> Optional[str]:
        """
        Get full document as HTML (with caching).

        Returns:
            HTML string or None if no document loaded
        """
        if self._cached_structure is None:
            return None

        if self._cached_html is None:
            self._cached_html = self.html_converter.document_to_html(
                self._cached_structure
            )

        return self._cached_html

    def get_section_preview(
        self,
        section_type: str,
        section_idx: int,
        context_size: int = 2,
    ) -> Optional[str]:
        """
        Get preview of a specific section with context.

        Args:
            section_type: 'paragraph' or 'table'
            section_idx: Index of the section
            context_size: Number of items before/after to include

        Returns:
            HTML string or None
        """
        if self._cached_structure is None:
            return None

        try:
            html_parts = []

            if section_type == "paragraph":
                # Get paragraphs with context
                sections = self._cached_structure.get("sections", [])
                start_idx = max(0, section_idx - context_size)
                end_idx = min(len(sections), section_idx + context_size + 1)

                context_sections = sections[start_idx:end_idx]
                html_parts.append(
                    self.html_converter.paragraphs_to_html(
                        context_sections,
                        highlight_idx=section_idx - start_idx,
                        context_range=0,
                    )
                )

            elif section_type == "table":
                # Get table with context
                tables = self._cached_structure.get("tables", [])
                if section_idx < len(tables):
                    table = tables[section_idx]
                    html_parts.append(self.html_converter.table_to_html(table))

            html = "\n".join(html_parts)
            return self._wrap_html(html)

        except Exception as e:
            self.logger.error(f"Error generating section preview: {e}")
            return None

    def get_change_context_html(
        self,
        change: Dict[str, Any],
        mapped_location: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """
        Get HTML showing change in document context.

        Args:
            change: Change dictionary from excel parser
            mapped_location: Mapped location info from change_mapper

        Returns:
            HTML string or None
        """
        if self._cached_structure is None:
            return None

        try:
            return self.html_converter.generate_change_preview_html(
                self._cached_structure, change, mapped_location
            )

        except Exception as e:
            self.logger.error(f"Error generating change context HTML: {e}")
            return None

    def find_location_by_text(
        self,
        search_text: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Find location of text in document.

        Args:
            search_text: Text to search for

        Returns:
            Dict with location info or None
        """
        if self._cached_structure is None:
            return None

        try:
            search_lower = search_text.lower()

            # Search in paragraphs
            sections = self._cached_structure.get("sections", [])
            for idx, section in enumerate(sections):
                section_text = section.get("text", "").lower()
                if search_lower in section_text:
                    return {
                        "type": "paragraph",
                        "index": idx,
                        "text": section.get("text", ""),
                        "level": section.get("level", 0),
                    }

            # Search in tables
            tables = self._cached_structure.get("tables", [])
            for table_idx, table in enumerate(tables):
                rows = table.get("rows", [])
                for row_idx, row in enumerate(rows):
                    cells = row.get("cells", [])
                    for col_idx, cell in enumerate(cells):
                        cell_text = cell.get("text", "").lower()
                        if search_lower in cell_text:
                            return {
                                "type": "table",
                                "table_index": table_idx,
                                "row_index": row_idx,
                                "col_index": col_idx,
                                "text": cell.get("text", ""),
                            }

            return None

        except Exception as e:
            self.logger.error(f"Error finding location by text: {e}")
            return None

    def get_header_context(self, location: Dict[str, Any]) -> Optional[str]:
        """
        Get header/context for a location (useful for breadcrumb navigation).

        Args:
            location: Location dict from find_location_by_text or mapped_location

        Returns:
            HTML string with context breadcrumb or None
        """
        if self._cached_structure is None:
            return None

        try:
            location_type = location.get("type", "paragraph")
            context_parts = []

            if location_type == "paragraph":
                # Find the heading above this paragraph
                section_idx = location.get("index", 0)
                sections = self._cached_structure.get("sections", [])

                # Search backwards for a heading
                for i in range(section_idx, -1, -1):
                    if i < len(sections):
                        section = sections[i]
                        level = section.get("level", 0)
                        if level > 0:
                            # Found a heading
                            heading_text = section.get("text", "")
                            context_parts.append(
                                f"<span class='breadcrumb-item'>{heading_text}</span>"
                            )
                            break

            elif location_type == "table":
                # Get surrounding heading
                sections = self._cached_structure.get("sections", [])
                if sections:
                    # Use first heading as context
                    for section in sections:
                        level = section.get("level", 0)
                        if level == 1:  # Main heading
                            heading_text = section.get("text", "")
                            context_parts.append(
                                f"<span class='breadcrumb-item'>{heading_text}</span>"
                            )
                            break

            if context_parts:
                breadcrumb = " > ".join(context_parts)
                return f'<div class="breadcrumb">{breadcrumb}</div>'

            return None

        except Exception as e:
            self.logger.error(f"Error generating header context: {e}")
            return None

    def get_document_stats(self) -> Optional[Dict[str, Any]]:
        """
        Get statistics about loaded document.

        Returns:
            Dict with paragraph count, table count, etc.
        """
        if self._cached_structure is None:
            return None

        try:
            return {
                "sections": len(self._cached_structure.get("sections", [])),
                "tables": len(self._cached_structure.get("tables", [])),
                "headings": len(
                    [
                        s
                        for s in self._cached_structure.get("sections", [])
                        if s.get("level", 0) > 0
                    ]
                ),
            }

        except Exception as e:
            self.logger.error(f"Error getting document stats: {e}")
            return None

    def _wrap_html(self, content_html: str) -> str:
        """
        Wrap content HTML with document styling.

        Args:
            content_html: Inner HTML content

        Returns:
            Complete HTML document
        """
        from core.html_converter import HTMLConverter

        converter = HTMLConverter()
        header = converter._get_html_header()
        footer = converter._get_html_footer()
        return f"{header}\n{content_html}\n{footer}"
