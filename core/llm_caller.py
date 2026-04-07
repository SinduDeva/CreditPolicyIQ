"""LLM integration module for CreditPolicyIQ."""
import logging
import json
from typing import Dict, Any, Optional
from pathlib import Path
from core.llm_provider import LLMProviderFactory
from utils.cache_manager import cache_manager
from config import config

logger = logging.getLogger(__name__)


class LLMCaller:
    """Handles LLM calls with provider abstraction for policy change processing."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        provider: str = "anthropic",
        model: Optional[str] = None,
    ):
        """
        Initialize LLM caller with configurable provider.

        Args:
            api_key: API key for the provider (uses config if not provided)
            provider: LLM provider to use ('anthropic', 'openai', 'mock')
            model: Model name (uses config default if not provided)
        """
        self.api_key = api_key or config.api_key
        self.provider_type = provider or getattr(config, "llm_provider", "anthropic")
        self.model = model or config.model
        self.max_tokens = config.max_tokens
        self.logger = logger

        # Create provider instance
        self.provider = LLMProviderFactory.create_provider(
            provider_type=self.provider_type,
            api_key=self.api_key,
            model=self.model,
        )

        if not self.provider.is_configured():
            self.logger.warning(
                f"LLM provider '{self.provider_type}' is not properly configured. "
                "Using mock provider for testing. "
                "Set API key to enable real LLM features."
            )
            # Fall back to mock provider
            self.provider = LLMProviderFactory.create_provider(provider_type="mock")

        self.logger.info(f"LLM Caller initialized with provider: {self.provider.get_provider_name()}")

    def translate_change(
        self, change_data: Dict[str, Any], context: str, master_docx_path: str
    ) -> Dict[str, Any]:
        """
        Translate change using configured LLM provider.

        Args:
            change_data: Change data from detector
            context: Additional context
            master_docx_path: Path to master document

        Returns:
            Dictionary with translation results
        """
        try:
            # Check cache first
            cache_key = self._get_cache_key(change_data)
            cached_result = cache_manager.get(cache_key)
            if cached_result:
                self.logger.info(f"Using cached result for change {cache_key[:20]}")
                return cached_result

            # Build prompts
            system_prompt = self._build_system_prompt()
            user_prompt = self._build_user_prompt(change_data, context)

            self.logger.debug(f"Calling LLM provider: {self.provider.get_provider_name()}")

            # Call provider
            result = self.provider.translate_change(
                change_data=change_data,
                context=context,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
            )

            # Check if provider returned an error
            if "error" in result and result.get("error"):
                self.logger.warning(
                    f"LLM provider returned error: {result['error']}. "
                    "Attempting mock fallback..."
                )
                # Fall back to mock provider
                mock_provider = LLMProviderFactory.create_provider(provider_type="mock")
                result = mock_provider.translate_change(
                    change_data=change_data,
                    context=context,
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                )

            # Cache the result
            cache_manager.set(cache_key, result)

            confidence = result.get("confidence_score", 0)
            is_mock = result.get("is_mock", False)
            mock_note = " (Mock - no API)" if is_mock else ""
            self.logger.info(
                f"Successfully translated change with confidence {confidence:.1%}{mock_note}"
            )
            return result

        except Exception as e:
            self.logger.error(f"Unexpected error in translate_change: {e}")
            return {
                "suggested_narrative": None,
                "format_type": "error",
                "confidence_score": 0,
                "reasoning": f"Error: {str(e)}",
                "error": "UNKNOWN_ERROR",
            }

    def _build_system_prompt(self) -> str:
        """
        Build system prompt for credit policy domain.

        Returns:
            System prompt string
        """
        return """You are an expert credit policy analyst specializing in underwriting policy documentation.
Your role is to help translate policy changes from various sources into clear, consistent credit policy narrative.

When analyzing policy changes:
1. Maintain technical accuracy of underwriting and credit criteria
2. Use consistent formatting and terminology across all policies
3. Consider the impact on risk assessment and underwriting decisions
4. Ensure changes are clearly documented with context
5. Provide confidence assessment of your interpretation

Always respond with a JSON object containing:
- suggested_narrative: The proposed policy text
- format_type: Either 'narrative', 'table', 'list', or 'technical'
- confidence_score: 0-1 indicating your confidence in the interpretation
- reasoning: Explanation of your suggestions and any concerns"""

    def _build_user_prompt(
        self, change_data: Dict[str, Any], context: str
    ) -> str:
        """
        Build user prompt for specific change.

        Args:
            change_data: Change data from detector
            context: Additional context

        Returns:
            User prompt string
        """
        original_data = change_data.get("original_data", {})
        match_details = change_data.get("match_details", {})

        prompt = f"""Please analyze and translate the following credit policy change:

Section ID: {original_data.get('Section_ID', 'N/A')}
Section Name: {original_data.get('Section_Name', 'N/A')}
Change Type: {original_data.get('Change_Type', 'N/A')}

Policy Content:
{original_data.get('Policy_Content', '')}

UW Technical Details:
{original_data.get('UW_Technical_Details', '')}

Notes:
{original_data.get('Notes', '')}

Matching Section: {match_details.get('section_title', 'N/A')}
Match Confidence: {match_details.get('similarity_score', 0):.1%}

Additional Context:
{context or 'No additional context provided'}

Please provide:
1. A clear, concise narrative for this policy change
2. The appropriate format type for presentation
3. Your confidence level (0-1) in this interpretation
4. Any concerns or clarifications needed

Respond with a JSON object containing the fields described in the system prompt."""

        return prompt

    def _parse_llm_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse JSON response from Claude API.

        Args:
            response_text: Raw response text from API

        Returns:
            Parsed response dictionary
        """
        try:
            # Try to find JSON in the response
            import json
            import re

            # Look for JSON block
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                parsed = json.loads(json_str)
                return {
                    "suggested_narrative": parsed.get("suggested_narrative"),
                    "format_type": parsed.get("format_type", "narrative"),
                    "confidence_score": float(
                        parsed.get("confidence_score", 0.5)
                    ),
                    "reasoning": parsed.get("reasoning", ""),
                }
            else:
                # Return raw response as narrative if no JSON found
                return {
                    "suggested_narrative": response_text,
                    "format_type": "narrative",
                    "confidence_score": 0.3,
                    "reasoning": "Response did not contain JSON, returned as raw text",
                }
        except Exception as e:
            self.logger.warning(f"Error parsing LLM response: {e}")
            return {
                "suggested_narrative": response_text,
                "format_type": "narrative",
                "confidence_score": 0.2,
                "reasoning": f"Parsing error: {str(e)}",
            }

    def _get_cache_key(self, change_data: Dict[str, Any]) -> str:
        """
        Generate cache key for change data.

        Args:
            change_data: Change data dictionary

        Returns:
            Cache key string
        """
        try:
            original = change_data.get("original_data", {})
            key_content = f"{original.get('Section_ID', '')}_{original.get('Section_Name', '')}_{original.get('Policy_Content', '')[:50]}"
            import hashlib

            return hashlib.md5(key_content.encode()).hexdigest()
        except Exception as e:
            self.logger.warning(f"Error generating cache key: {e}")
            return "unknown_change"
