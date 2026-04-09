"""Streamlit component for displaying Word document previews with change highlighting."""
import streamlit as st
from typing import Dict, Any, Optional, List
import io

from core.document_preview import DocumentPreview
from core.html_converter import HTMLConverter


def render_document_preview(
    document_preview: DocumentPreview,
    title: str = "Document Preview",
    height: int = 600,
) -> None:
    """
    Render full document preview in Streamlit.

    Args:
        document_preview: DocumentPreview instance with loaded document
        title: Title to display
        height: Height of preview container
    """
    st.subheader(title)

    # Get document HTML
    html_content = document_preview.get_full_document_html()

    if not html_content:
        st.warning("No document loaded")
        return

    # Display stats
    stats = document_preview.get_document_stats()
    if stats:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Paragraphs", stats.get("sections", 0))
        with col2:
            st.metric("Tables", stats.get("tables", 0))
        with col3:
            st.metric("Headings", stats.get("headings", 0))

    # Display HTML in iframe
    st.components.v1.html(html_content, height=height, scrolling=True)


def render_change_with_context(
    document_preview: DocumentPreview,
    change: Dict[str, Any],
    mapped_location: Optional[Dict[str, Any]] = None,
    title: str = "Change Context",
    height: int = 500,
) -> None:
    """
    Render a change with its document context.

    Args:
        document_preview: DocumentPreview instance
        change: Change dictionary
        mapped_location: Optional mapped location
        title: Title to display
        height: Preview height
    """
    st.subheader(title)

    # Display change info
    col1, col2, col3 = st.columns(3)
    with col1:
        change_type = change.get("type", "UNKNOWN")
        type_color = {
            "NEW": "🟢",
            "MODIFIED": "🟡",
            "DELETED": "🔴",
        }.get(change_type, "⚪")
        st.write(f"{type_color} **Type**: {change_type}")

    with col2:
        confidence = mapped_location.get("confidence", 0) if mapped_location else 0
        st.write(f"📊 **Confidence**: {confidence:.0%}")

    with col3:
        location = mapped_location.get("type", "Unknown") if mapped_location else "Not mapped"
        st.write(f"📍 **Location**: {location}")

    st.divider()

    # Display change content
    st.write("**Change Content**:")
    change_content = change.get("content", "")
    st.code(change_content, language="text")

    # Display context if available
    context = change.get("context", {})
    if context:
        st.write("**Context**:")
        col1, col2 = st.columns(2)
        with col1:
            before = context.get("before", "")
            if before:
                st.write("_Before:_")
                st.text(before)

        with col2:
            after = context.get("after", "")
            if after:
                st.write("_After:_")
                st.text(after)

    st.divider()

    # Display mapped location context
    if mapped_location:
        st.write("**Suggested Location in Document**:")
        html_content = document_preview.get_change_context_html(change, mapped_location)
        if html_content:
            st.components.v1.html(html_content, height=height, scrolling=True)
        else:
            st.info("Could not generate preview for this location")
    else:
        st.info("No location mapping available")


def render_side_by_side_comparison(
    document_preview: DocumentPreview,
    original_location: Dict[str, Any],
    suggested_change: str,
    height: int = 400,
) -> None:
    """
    Render side-by-side comparison of original and suggested text.

    Args:
        document_preview: DocumentPreview instance
        original_location: Location of original text in document
        suggested_change: Suggested modification text
        height: Height of comparison area
    """
    st.subheader("Change Comparison")

    col1, col2 = st.columns(2)

    with col1:
        st.write("**Current Master Document**:")
        section_type = original_location.get("type", "paragraph")
        section_idx = original_location.get("index", 0)

        html_current = document_preview.get_section_preview(section_type, section_idx)
        if html_current:
            st.components.v1.html(html_current, height=height, scrolling=True)
        else:
            st.warning("Could not load current text")

    with col2:
        st.write("**Suggested Modification**:")
        # Create HTML for suggested text
        html_suggested = f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    padding: 20px;
                    background-color: #f5f5f5;
                }}
                .suggestion {{
                    background-color: #e8f4f8;
                    padding: 16px;
                    border-left: 4px solid #2196f3;
                    border-radius: 4px;
                    line-height: 1.6;
                }}
            </style>
        </head>
        <body>
            <div class="suggestion">
                {suggested_change}
            </div>
        </body>
        </html>
        """
        st.components.v1.html(html_suggested, height=height, scrolling=True)


def render_document_breadcrumb(
    document_preview: DocumentPreview,
    location: Dict[str, Any],
) -> None:
    """
    Render breadcrumb navigation for document location.

    Args:
        document_preview: DocumentPreview instance
        location: Location dictionary
    """
    breadcrumb_html = document_preview.get_header_context(location)
    if breadcrumb_html:
        st.components.v1.html(f"""
        <style>
            .breadcrumb {{
                font-size: 14px;
                color: #666;
                margin: 10px 0;
            }}
            .breadcrumb-item {{
                margin-right: 8px;
            }}
        </style>
        {breadcrumb_html}
        """)


def render_search_and_navigate(
    document_preview: DocumentPreview,
) -> Optional[Dict[str, Any]]:
    """
    Render search and navigation controls for document.

    Args:
        document_preview: DocumentPreview instance

    Returns:
        Selected location or None
    """
    st.subheader("Find in Document")

    search_text = st.text_input("Search for text in document:", placeholder="Enter search term...")

    if search_text and len(search_text) > 2:
        location = document_preview.find_location_by_text(search_text)

        if location:
            st.success(f"Found: {location.get('text', '')[:100]}")
            return location
        else:
            st.warning("Text not found in document")

    return None


def render_document_stats_dashboard(
    document_preview: DocumentPreview,
) -> None:
    """
    Render document statistics dashboard.

    Args:
        document_preview: DocumentPreview instance
    """
    st.subheader("Document Statistics")

    stats = document_preview.get_document_stats()

    if not stats:
        st.warning("No document loaded")
        return

    # Create metrics
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Total Sections",
            stats.get("sections", 0),
            delta="paragraphs and content areas",
        )

    with col2:
        st.metric(
            "Tables",
            stats.get("tables", 0),
            delta="structured data",
        )

    with col3:
        st.metric(
            "Headings",
            stats.get("headings", 0),
            delta="structure levels",
        )

    # Display additional info
    st.info(
        f"📋 Document contains {stats.get('sections', 0)} sections organized in "
        f"{stats.get('headings', 0)} heading levels with {stats.get('tables', 0)} structured tables."
    )


def download_preview_as_html(
    document_preview: DocumentPreview,
    filename: str = "document_preview.html",
) -> None:
    """
    Provide download button for document preview as HTML.

    Args:
        document_preview: DocumentPreview instance
        filename: Filename for download
    """
    html_content = document_preview.get_full_document_html()

    if html_content:
        st.download_button(
            label="📥 Download Preview as HTML",
            data=html_content,
            file_name=filename,
            mime="text/html",
        )
    else:
        st.warning("No preview available to download")


def display_change_suggestion(
    change: Dict[str, Any],
    suggestion: Dict[str, Any],
    show_explanation: bool = True,
) -> None:
    """
    Display a change and its LLM suggestion.

    Args:
        change: Change dictionary
        suggestion: Suggestion dictionary
        show_explanation: Whether to show explanation
    """
    # Create two columns: change and suggestion
    col1, col2 = st.columns([1, 1])

    with col1:
        st.write("**Original Change**:")
        change_type = change.get("type", "UNKNOWN")
        st.caption(f"Type: {change_type}")
        st.code(change.get("content", ""), language="text")

    with col2:
        st.write("**Suggested Modification**:")
        confidence = suggestion.get("confidence", 0.5)
        st.caption(f"Confidence: {confidence:.0%}")
        st.code(suggestion.get("suggestion_text", ""), language="text")

    # Show explanation if available
    if show_explanation and suggestion.get("explanation"):
        st.info(f"💡 {suggestion.get('explanation')}")
