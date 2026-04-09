"""Generate LLM-powered suggestions for policy document modifications."""
import logging
from typing import Dict, List, Any, Optional
import json

from config import config
from core.llm_provider import get_llm_provider

logger = logging.getLogger(__name__)


class LLMSuggestionGenerator:
    """Generate intelligent suggestions for document changes using LLM."""

    def __init__(self):
        """Initialize suggestion generator."""
        self.logger = logger
        self.llm_provider = get_llm_provider()

    def generate_modification_suggestion(
        self,
        change: Dict[str, Any],
        original_text: Optional[str] = None,
        document_context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate a suggestion for how to modify the master document.

        Args:
            change: Change dictionary from excel parser
            original_text: Original text from master document
            document_context: Context from surrounding document content

        Returns:
            Suggestion dictionary with proposed modification
        """
        try:
            change_type = change.get("type", "CHANGE")
            change_content = change.get("content", "")
            context = change.get("context", {})

            if not self.llm_provider:
                return self._get_no_provider_suggestion(change)

            # Build the prompt
            prompt = self._build_suggestion_prompt(
                change_type, change_content, original_text, document_context, context
            )

            # Call LLM
            response = self.llm_provider.call(
                prompt,
                max_tokens=config.max_tokens,
                temperature=0.3,  # Lower temperature for consistency
            )

            if not response:
                return self._get_fallback_suggestion(change)

            # Parse the response
            suggestion = self._parse_suggestion_response(response, change_type, change_content)

            self.logger.debug(f"Generated suggestion for change: {suggestion}")
            return suggestion

        except Exception as e:
            self.logger.error(f"Error generating suggestion: {e}")
            return self._get_fallback_suggestion(change)

    def generate_batch_suggestions(
        self,
        changes: List[Dict[str, Any]],
        original_texts: Optional[List[Optional[str]]] = None,
        document_context: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Generate suggestions for multiple changes in batch.

        Args:
            changes: List of change dictionaries
            original_texts: List of original texts (optional)
            document_context: Shared document context

        Returns:
            List of suggestion dictionaries
        """
        try:
            if not self.llm_provider:
                return [self._get_no_provider_suggestion(c) for c in changes]

            suggestions = []

            # Group changes by type for efficient batch processing
            changes_by_type = {"NEW": [], "MODIFIED": [], "DELETED": []}
            for idx, change in enumerate(changes):
                change_type = change.get("type", "CHANGE")
                if change_type in changes_by_type:
                    changes_by_type[change_type].append((idx, change))

            # Process each type
            for change_type, type_changes in changes_by_type.items():
                if not type_changes:
                    continue

                # Generate suggestions for this type
                for idx, change in type_changes:
                    original_text = (
                        original_texts[idx] if original_texts and idx < len(original_texts) else None
                    )
                    suggestion = self.generate_modification_suggestion(
                        change, original_text, document_context
                    )
                    suggestions.append((idx, suggestion))

            # Sort by original index
            suggestions.sort(key=lambda x: x[0])
            return [s[1] for s in suggestions]

        except Exception as e:
            self.logger.error(f"Error generating batch suggestions: {e}")
            return [self._get_fallback_suggestion(c) for c in changes]

    def _build_suggestion_prompt(
        self,
        change_type: str,
        change_content: str,
        original_text: Optional[str],
        document_context: Optional[str],
        context: Dict[str, Any],
    ) -> str:
        """Build the prompt for LLM suggestion generation."""
        prompt_parts = [
            "You are a credit policy document expert. Generate a professional modification suggestion for the master document.\n"
        ]

        # Add context if available
        if document_context:
            prompt_parts.append(f"Document Context:\n{document_context}\n")

        # Add the change information
        prompt_parts.append(f"Change Type: {change_type}")
        prompt_parts.append(f"Change Content: {change_content}")

        if original_text:
            prompt_parts.append(f"Current Master Document Text: {original_text}")

        # Add surrounding context
        context_before = context.get("before", "")
        context_after = context.get("after", "")
        if context_before:
            prompt_parts.append(f"Context (Before): {context_before}")
        if context_after:
            prompt_parts.append(f"Context (After): {context_after}")

        # Add task instruction based on change type
        if change_type == "NEW":
            prompt_parts.append(
                "Task: Generate professional language to ADD this new policy provision to the document. "
                "Provide the exact text to insert, ensuring it fits naturally with the document tone and style. "
                "Format: Return ONLY the text to add, no explanations."
            )
        elif change_type == "MODIFIED" or change_type == "CHANGE":
            prompt_parts.append(
                "Task: Generate professional language to MODIFY/REPLACE the current text. "
                "Maintain document tone and policy format. "
                "Format: Return ONLY the replacement text, no explanations."
            )
        elif change_type == "DELETED":
            prompt_parts.append(
                "Task: Confirm this text should be REMOVED from the document. "
                "Format: Return 'DELETE' if removal is appropriate, or provide replacement text if needed."
            )
        else:
            prompt_parts.append(
                "Task: Generate a professional policy language suggestion. "
                "Format: Return ONLY the text suggestion, no explanations."
            )

        return "\n".join(prompt_parts)

    def _parse_suggestion_response(
        self, response: str, change_type: str, change_content: str
    ) -> Dict[str, Any]:
        """Parse LLM response into structured suggestion."""
        try:
            # Clean the response
            suggestion_text = response.strip()

            return {
                "suggestion_text": suggestion_text,
                "change_type": change_type,
                "original_content": change_content,
                "confidence": 0.8,  # LLM generated
                "source": "llm",
                "explanation": None,
            }

        except Exception as e:
            self.logger.error(f"Error parsing suggestion response: {e}")
            return self._get_fallback_suggestion(
                {"type": change_type, "content": change_content}
            )

    def _get_fallback_suggestion(self, change: Dict[str, Any]) -> Dict[str, Any]:
        """Get fallback suggestion when LLM fails or is unavailable."""
        change_type = change.get("type", "CHANGE")
        change_content = change.get("content", "")

        fallback_text = {
            "NEW": f"[ADD] {change_content}",
            "MODIFIED": f"Replace with: {change_content}",
            "DELETED": f"[REMOVE] {change_content}",
            "CHANGE": change_content,
        }.get(change_type, change_content)

        return {
            "suggestion_text": fallback_text,
            "change_type": change_type,
            "original_content": change_content,
            "confidence": 0.5,
            "source": "fallback",
            "explanation": "Fallback suggestion (LLM unavailable)",
        }

    def _get_no_provider_suggestion(self, change: Dict[str, Any]) -> Dict[str, Any]:
        """Get suggestion when LLM provider is not available."""
        return {
            "suggestion_text": change.get("content", ""),
            "change_type": change.get("type", "CHANGE"),
            "original_content": change.get("content", ""),
            "confidence": 0.0,
            "source": "mock",
            "explanation": "No LLM provider configured. Using mock provider.",
        }

    def explain_change(
        self,
        change: Dict[str, Any],
        original_text: Optional[str] = None,
    ) -> str:
        """
        Generate a human-readable explanation of a change.

        Args:
            change: Change dictionary
            original_text: Original master document text

        Returns:
            Explanation string
        """
        try:
            if not self.llm_provider:
                return f"Change type: {change.get('type', 'UNKNOWN')}. Content: {change.get('content', '')}"

            change_type = change.get("type", "CHANGE")
            change_content = change.get("content", "")

            prompt = f"""Explain this policy document change in 1-2 sentences:
Type: {change_type}
Content: {change_content}
{f'Current text: {original_text}' if original_text else ''}

Keep explanation brief and professional."""

            response = self.llm_provider.call(prompt, max_tokens=100, temperature=0.3)

            return response if response else f"Change: {change_content}"

        except Exception as e:
            self.logger.debug(f"Error explaining change: {e}")
            return f"Change: {change.get('content', '')}"

    def validate_suggestion(
        self,
        change: Dict[str, Any],
        suggestion: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Validate if a suggestion makes sense for the change.

        Args:
            change: Original change
            suggestion: Generated suggestion

        Returns:
            Validation result with confidence score
        """
        try:
            change_type = change.get("type", "CHANGE")
            suggestion_text = suggestion.get("suggestion_text", "")

            validation = {
                "is_valid": True,
                "confidence": suggestion.get("confidence", 0.5),
                "issues": [],
            }

            # Basic validation checks
            if not suggestion_text or len(suggestion_text.strip()) == 0:
                validation["is_valid"] = False
                validation["issues"].append("Empty suggestion text")

            if change_type == "DELETED" and "DELETE" not in suggestion_text.upper():
                validation["issues"].append("Suggestion may not properly handle deletion")

            if change_type == "NEW" and len(suggestion_text) < len(change.get("content", "")):
                validation["issues"].append("Suggestion may be incomplete")

            return validation

        except Exception as e:
            self.logger.error(f"Error validating suggestion: {e}")
            return {
                "is_valid": False,
                "confidence": 0.0,
                "issues": [str(e)],
            }
