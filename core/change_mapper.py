"""
Intelligent change mapper for matching Excel changes to master document sections.
Uses multiple strategies to find the best location for each change.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from difflib import SequenceMatcher
import re

logger = logging.getLogger(__name__)


class ChangeMapper:
    """
    Maps Excel changes to master document sections using intelligent matching.

    Strategies:
    1. Keyword matching - Find section by keywords in change content
    2. Fuzzy text matching - Compare change text with document sections
    3. Context matching - Use surrounding text to find location
    4. Change type matching - Map NEW/MODIFIED/DELETED to appropriate sections
    """

    def __init__(self):
        """Initialize change mapper."""
        self.logger = logger
        # Common keywords for each change type
        self.section_keywords = {
            "coverage": ["coverage", "benefit", "covered", "benefits"],
            "deductible": ["deductible", "out of pocket", "oop"],
            "copay": ["copay", "co-pay", "copayment"],
            "limit": ["limit", "maximum", "cap", "threshold"],
            "network": ["network", "in-network", "out-of-network", "provider"],
            "claim": ["claim", "filing", "submit", "reimbursement"],
            "exclusion": ["exclusion", "excluded", "not covered"],
            "term": ["term", "duration", "period", "effective"],
            "mental": ["mental", "behavioral", "psychiatric", "psychology"],
            "dental": ["dental", "teeth", "oral", "dentist"],
            "vision": ["vision", "eye", "glasses", "contact", "optical"],
            "pharmacy": ["pharmacy", "prescription", "drug", "medication"],
            "wellness": ["wellness", "preventive", "screening"],
        }

    def map_change_to_section(
        self,
        change: Dict[str, Any],
        master_structure: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Map a change to the best matching section in master document.

        Args:
            change: Change from Excel with content and context
            master_structure: Master document structure

        Returns:
            Mapping details with section, confidence, and strategy used
        """
        change_content = change.get("Policy_Content", "").lower()
        change_context = change.get("Context", "").lower()
        change_type = change.get("Change_Type", "OTHER")

        if not change_content:
            return {
                "matched": False,
                "confidence": 0,
                "reason": "No content to match",
            }

        # Try multiple matching strategies
        strategies = [
            ("keyword_matching", self._keyword_match(change_content, change_context, master_structure)),
            ("content_similarity", self._content_match(change_content, master_structure)),
            ("context_matching", self._context_match(change_content, change_context, master_structure)),
        ]

        # Find best match from all strategies
        best_match = None
        best_confidence = 0
        best_strategy = None

        for strategy_name, result in strategies:
            if result and result.get("confidence", 0) > best_confidence:
                best_confidence = result.get("confidence", 0)
                best_match = result
                best_strategy = strategy_name

        if best_match:
            best_match["strategy_used"] = best_strategy
            best_match["confidence"] = best_confidence
            self.logger.info(
                f"Mapped change to section '{best_match.get('section_title')}' "
                f"using {best_strategy} (confidence: {best_confidence:.1%})"
            )
            return best_match
        else:
            return {
                "matched": False,
                "confidence": 0,
                "reason": "No matching section found",
                "suggestions": self._suggest_sections(change_content, master_structure),
            }

    def _keyword_match(
        self,
        content: str,
        context: str,
        master_structure: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """Match based on keywords extracted from change."""
        combined_text = f"{context} {content}"
        extracted_keywords = self._extract_keywords(combined_text)

        if not extracted_keywords:
            return None

        best_match = None
        best_score = 0

        sections = master_structure.get("sections", [])
        for section_idx, section in enumerate(sections):
            section_title = section.get("title", "").lower()
            section_text = self._get_section_text(section, master_structure)

            # Count matching keywords
            matching_keywords = [
                kw for kw in extracted_keywords if kw in section_title or kw in section_text
            ]

            if matching_keywords:
                score = len(matching_keywords) / len(extracted_keywords)
                if score > best_score:
                    best_score = score
                    best_match = {
                        "matched": True,
                        "section_index": section_idx,
                        "section_title": section.get("title"),
                        "confidence": min(score, 0.95),  # Cap at 95%
                        "matching_keywords": matching_keywords,
                        "start_para_idx": section.get("start_para_idx"),
                    }

        return best_match if best_score > 0.3 else None

    def _content_match(
        self,
        content: str,
        master_structure: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """Match using fuzzy text similarity."""
        best_match = None
        best_score = 0

        sections = master_structure.get("sections", [])
        for section_idx, section in enumerate(sections):
            section_text = self._get_section_text(section, master_structure)

            # Find best matching paragraph in section
            paragraphs = section.get("paragraphs", [])
            for para_idx in paragraphs:
                para = master_structure.get("paragraphs", [{}])[para_idx] if para_idx < len(
                    master_structure.get("paragraphs", [])
                ) else {}
                para_text = para.get("text", "").lower()

                score = self._similarity_score(content, para_text)

                if score > best_score:
                    best_score = score
                    best_match = {
                        "matched": True,
                        "section_index": section_idx,
                        "section_title": section.get("title"),
                        "paragraph_index": para_idx,
                        "confidence": score,
                        "matching_text": para_text[:100],
                        "start_para_idx": section.get("start_para_idx"),
                    }

        return best_match if best_score > 0.3 else None

    def _context_match(
        self,
        content: str,
        context: str,
        master_structure: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """Match using context from surrounding cells."""
        if not context:
            return None

        best_match = None
        best_score = 0

        sections = master_structure.get("sections", [])
        for section_idx, section in enumerate(sections):
            section_text = self._get_section_text(section, master_structure)

            # Match context phrases
            context_phrases = [p.strip() for p in context.split(",") if p.strip()]
            matching_phrases = [
                p for p in context_phrases if len(p) > 3 and p in section_text.lower()
            ]

            if matching_phrases:
                score = len(matching_phrases) / max(len(context_phrases), 1)

                # Also consider content similarity within the section
                content_score = self._similarity_score(content, section_text)
                combined_score = (score * 0.4) + (content_score * 0.6)

                if combined_score > best_score:
                    best_score = combined_score
                    best_match = {
                        "matched": True,
                        "section_index": section_idx,
                        "section_title": section.get("title"),
                        "confidence": min(combined_score, 0.9),
                        "matching_phrases": matching_phrases,
                        "start_para_idx": section.get("start_para_idx"),
                    }

        return best_match if best_score > 0.3 else None

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract relevant keywords from text."""
        keywords = []

        # Check against predefined keyword groups
        for category, keyword_list in self.section_keywords.items():
            for keyword in keyword_list:
                if keyword in text.lower():
                    keywords.append(keyword)

        # Also extract capitalized terms (section names)
        words = text.split()
        for word in words:
            if len(word) > 4 and word[0].isupper():
                keywords.append(word.lower())

        return list(set(keywords))[:10]  # Return unique keywords, max 10

    def _similarity_score(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts (0-1)."""
        if not text1 or not text2:
            return 0.0

        # Use SequenceMatcher for ratio
        matcher = SequenceMatcher(None, text1, text2)
        return matcher.ratio()

    def _get_section_text(
        self, section: Dict[str, Any], master_structure: Dict[str, Any]
    ) -> str:
        """Get all text from a section."""
        section_text = section.get("title", "")

        # Add all paragraph text in section
        paragraphs = section.get("paragraphs", [])
        for para_idx in paragraphs:
            if para_idx < len(master_structure.get("paragraphs", [])):
                para = master_structure["paragraphs"][para_idx]
                section_text += " " + para.get("text", "")

        return section_text.lower()

    def _suggest_sections(
        self, content: str, master_structure: Dict[str, Any], limit: int = 3
    ) -> List[str]:
        """Suggest top sections that might be relevant."""
        suggestions = []

        sections = master_structure.get("sections", [])
        scores = []

        for section in sections:
            section_text = self._get_section_text(section, master_structure)
            score = self._similarity_score(content, section_text)
            scores.append((section.get("title"), score))

        # Sort by score and return top suggestions
        scores.sort(key=lambda x: x[1], reverse=True)
        return [title for title, score in scores[:limit] if score > 0.1]
