"""Convert Word document structures to HTML for preview rendering."""
import logging
from typing import Dict, List, Any, Optional
from html import escape

logger = logging.getLogger(__name__)


class HTMLConverter:
    """Convert extracted Word document structures to styled HTML."""

    def __init__(self):
        """Initialize HTML converter."""
        self.logger = logger

    def table_to_html(
        self,
        table: Dict[str, Any],
        highlight_cell: Optional[Dict[str, int]] = None,
        highlight_row: Optional[int] = None,
    ) -> str:
        """
        Convert extracted table to HTML.

        Args:
            table: Table dictionary from table_extractor
            highlight_cell: Dict with 'row' and 'col' to highlight specific cell
            highlight_row: Row index to highlight entire row

        Returns:
            HTML string with styled table
        """
        try:
            html_parts = ['<div class="table-container">']
            html_parts.append('<table class="word-table">')

            rows = table.get("rows", [])

            for row_idx, row in enumerate(rows):
                row_class = "table-header" if row_idx == 0 else ""
                if highlight_row is not None and row_idx == highlight_row:
                    row_class = "row-highlight"

                html_parts.append(f'<tr class="{row_class}">')

                cells = row.get("cells", [])
                for col_idx, cell in enumerate(cells):
                    # Determine cell highlighting
                    cell_class = "table-cell"
                    if row_idx == 0:
                        cell_class += " header-cell"
                    if highlight_cell and (
                        highlight_cell.get("row") == row_idx
                        and highlight_cell.get("col") == col_idx
                    ):
                        cell_class = "cell-highlight"

                    # Get cell content
                    text = cell.get("text", "")
                    text_escaped = escape(text)

                    # Check for merged cells
                    merge_info = cell.get("merge_info", {})
                    colspan = ""
                    rowspan = ""

                    if merge_info:
                        h_span = merge_info.get("horizontal_span", 1)
                        if h_span > 1:
                            colspan = f' colspan="{h_span}"'

                    # Get background color if any
                    shading = cell.get("shading")
                    style = ""
                    if shading:
                        style = f' style="background-color: #{shading};"'

                    html_parts.append(
                        f'<td class="{cell_class}"{colspan}{style}>{text_escaped}</td>'
                    )

                html_parts.append("</tr>")

            html_parts.append("</table>")
            html_parts.append("</div>")

            return "\n".join(html_parts)

        except Exception as e:
            self.logger.error(f"Error converting table to HTML: {e}")
            return "<p>Error rendering table</p>"

    def paragraphs_to_html(
        self,
        paragraphs: List[Dict[str, Any]],
        highlight_idx: Optional[int] = None,
        context_range: int = 2,
    ) -> str:
        """
        Convert extracted paragraphs to HTML with styling.

        Args:
            paragraphs: List of paragraph dicts from docx_handler
            highlight_idx: Paragraph index to highlight
            context_range: Number of paragraphs before/after to show

        Returns:
            HTML string with styled paragraphs
        """
        try:
            html_parts = ['<div class="paragraph-container">']

            if highlight_idx is not None:
                # Show context around highlighted paragraph
                start_idx = max(0, highlight_idx - context_range)
                end_idx = min(len(paragraphs), highlight_idx + context_range + 1)
            else:
                start_idx = 0
                end_idx = len(paragraphs)

            for idx in range(start_idx, end_idx):
                if idx >= len(paragraphs):
                    break

                para = paragraphs[idx]
                para_class = "paragraph"

                if highlight_idx is not None and idx == highlight_idx:
                    para_class = "paragraph paragraph-highlight"

                # Get heading level if exists
                level = para.get("level", 0)
                if level > 0:
                    para_class += f" heading-level-{level}"

                # Get text content
                text = para.get("text", "")
                text_escaped = escape(text)

                # Create appropriate HTML element
                if level > 0:
                    tag = f"h{min(level + 1, 6)}"
                else:
                    tag = "p"

                html_parts.append(f"<{tag} class='{para_class}'>{text_escaped}</{tag}>")

            html_parts.append("</div>")

            return "\n".join(html_parts)

        except Exception as e:
            self.logger.error(f"Error converting paragraphs to HTML: {e}")
            return "<p>Error rendering content</p>"

    def document_to_html(
        self,
        document_structure: Dict[str, Any],
        highlight: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Convert full document structure to HTML.

        Args:
            document_structure: Full document from docx_handler
            highlight: Optional highlight spec with 'type' and location info

        Returns:
            Complete HTML document string
        """
        try:
            html_parts = [self._get_html_header()]

            # Process paragraphs and tables in order
            content = document_structure.get("content", [])

            for item in content:
                item_type = item.get("type", "paragraph")

                if item_type == "paragraph":
                    para_html = self.paragraphs_to_html(
                        [item],
                        highlight_idx=0 if highlight and highlight.get("type") == "paragraph" else None,
                    )
                    html_parts.append(para_html)

                elif item_type == "table":
                    highlight_cell = None
                    if highlight and highlight.get("type") == "table":
                        highlight_cell = {
                            "row": highlight.get("row"),
                            "col": highlight.get("col"),
                        }
                    table_html = self.table_to_html(item, highlight_cell=highlight_cell)
                    html_parts.append(table_html)

            html_parts.append(self._get_html_footer())

            return "\n".join(html_parts)

        except Exception as e:
            self.logger.error(f"Error converting document to HTML: {e}")
            return self._get_error_html(str(e))

    def _get_html_header(self) -> str:
        """Get HTML header with styling."""
        return """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Document Preview</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f5f5;
            padding: 20px;
        }

        .document-container {
            background-color: white;
            max-width: 900px;
            margin: 0 auto;
            padding: 40px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            border-radius: 4px;
        }

        .paragraph-container {
            margin-bottom: 20px;
        }

        p {
            margin-bottom: 12px;
            text-align: justify;
        }

        h1, h2, h3, h4, h5, h6 {
            margin-top: 24px;
            margin-bottom: 12px;
            font-weight: 600;
            color: #222;
        }

        h1 { font-size: 28px; }
        h2 { font-size: 24px; }
        h3 { font-size: 20px; }
        h4 { font-size: 18px; }
        h5 { font-size: 16px; }
        h6 { font-size: 14px; }

        .heading-level-1 {
            font-size: 20px;
            color: #1a5490;
            border-bottom: 2px solid #e0e0e0;
            padding-bottom: 8px;
        }

        .heading-level-2 {
            font-size: 18px;
            color: #2d7bb8;
            margin-left: 20px;
        }

        .heading-level-3 {
            font-size: 16px;
            color: #4a90a4;
            margin-left: 40px;
        }

        .table-container {
            margin: 24px 0;
            overflow-x: auto;
        }

        .word-table {
            width: 100%;
            border-collapse: collapse;
            border: 1px solid #ddd;
            margin-bottom: 20px;
        }

        .word-table td {
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }

        .table-header .header-cell {
            background-color: #4a90a4;
            color: white;
            font-weight: bold;
            text-align: center;
        }

        .table-header {
            background-color: #f0f0f0;
        }

        .cell-highlight {
            background-color: #fff3cd !important;
            border: 2px solid #ffc107 !important;
            font-weight: 500;
        }

        .row-highlight {
            background-color: #e8f4f8;
        }

        .row-highlight td {
            background-color: #e8f4f8;
        }

        .paragraph-highlight {
            background-color: #fff3cd;
            padding: 12px;
            border-left: 4px solid #ffc107;
            margin-left: -12px;
            margin-right: -12px;
            padding-left: 20px;
        }

        .error {
            color: #d32f2f;
            background-color: #ffebee;
            padding: 16px;
            border-radius: 4px;
            border-left: 4px solid #d32f2f;
        }
    </style>
</head>
<body>
<div class="document-container">
"""

    def _get_html_footer(self) -> str:
        """Get HTML footer."""
        return """</div>
</body>
</html>
"""

    def _get_error_html(self, error_message: str) -> str:
        """Get HTML error page."""
        error_escaped = escape(error_message)
        return f"""{self._get_html_header()}
<div class="error">
    <strong>Error rendering document:</strong><br>
    {error_escaped}
</div>
{self._get_html_footer()}"""

    def generate_change_preview_html(
        self,
        document_structure: Dict[str, Any],
        change: Dict[str, Any],
        mapped_section: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Generate HTML preview showing change context in document.

        Args:
            document_structure: Full document from docx_handler
            change: Change dictionary from intelligent_excel_parser
            mapped_section: Mapped section from change_mapper

        Returns:
            HTML showing the change in context
        """
        try:
            html_parts = [self._get_html_header()]

            # Add change info box
            change_content = escape(change.get("content", ""))
            change_type = change.get("type", "CHANGE")
            change_type_color = {
                "NEW": "#4caf50",
                "MODIFIED": "#ff9800",
                "DELETED": "#f44336",
            }.get(change_type, "#2196f3")

            html_parts.append(f"""
<div style="background-color: {change_type_color}; color: white; padding: 16px; border-radius: 4px; margin-bottom: 24px;">
    <strong>Change [{change_type}]:</strong> {change_content}
</div>
""")

            # Add document context if mapped
            if mapped_section:
                section_type = mapped_section.get("type", "paragraph")
                confidence = mapped_section.get("confidence", 0)

                html_parts.append(f"""
<div style="background-color: #e3f2fd; padding: 12px; border-radius: 4px; margin-bottom: 24px; border-left: 4px solid #2196f3;">
    <strong>Suggested Location:</strong> {section_type} (Confidence: {confidence:.0%})
</div>
""")

                # Show context from mapped section
                if section_type == "paragraph":
                    para_idx = mapped_section.get("paragraph_idx", 0)
                    content = document_structure.get("content", [])
                    if para_idx < len(content):
                        para_html = self.paragraphs_to_html(
                            [content[para_idx]], highlight_idx=0, context_range=2
                        )
                        html_parts.append(para_html)

                elif section_type == "table":
                    table_idx = mapped_section.get("table_idx", 0)
                    row_idx = mapped_section.get("row_idx", 0)
                    col_idx = mapped_section.get("col_idx", 0)

                    content = document_structure.get("content", [])
                    if table_idx < len(content):
                        table_html = self.table_to_html(
                            content[table_idx],
                            highlight_cell={"row": row_idx, "col": col_idx},
                        )
                        html_parts.append(table_html)

            html_parts.append(self._get_html_footer())

            return "\n".join(html_parts)

        except Exception as e:
            self.logger.error(f"Error generating change preview HTML: {e}")
            return self._get_error_html(str(e))
