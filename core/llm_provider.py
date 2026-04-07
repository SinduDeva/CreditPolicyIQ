"""Abstract LLM provider interface and implementations."""
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def translate_change(
        self,
        change_data: Dict[str, Any],
        context: str,
        system_prompt: str,
        user_prompt: str,
    ) -> Dict[str, Any]:
        """
        Translate a change using the LLM provider.

        Args:
            change_data: Change data dictionary
            context: Additional context
            system_prompt: System prompt for the LLM
            user_prompt: User prompt with change details

        Returns:
            Dictionary with translation results
        """
        pass

    @abstractmethod
    def is_configured(self) -> bool:
        """Check if the provider is properly configured."""
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """Get the provider name."""
        pass


class AnthropicProvider(LLMProvider):
    """Anthropic Claude API provider."""

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-5-sonnet-20241022"):
        """
        Initialize Anthropic provider.

        Args:
            api_key: Anthropic API key
            model: Model name to use
        """
        self.api_key = api_key
        self.model = model
        self.logger = logger

        if self.api_key:
            try:
                import anthropic

                self.client = anthropic.Anthropic(api_key=self.api_key)
                self.logger.info("Anthropic provider initialized successfully")
            except Exception as e:
                self.logger.error(f"Failed to initialize Anthropic client: {e}")
                self.client = None
        else:
            self.client = None

    def is_configured(self) -> bool:
        """Check if Anthropic provider is configured."""
        return self.client is not None and self.api_key is not None

    def get_provider_name(self) -> str:
        """Get provider name."""
        return "Anthropic"

    def translate_change(
        self,
        change_data: Dict[str, Any],
        context: str,
        system_prompt: str,
        user_prompt: str,
    ) -> Dict[str, Any]:
        """
        Translate change using Anthropic Claude API.

        Args:
            change_data: Change data dictionary
            context: Additional context
            system_prompt: System prompt
            user_prompt: User prompt

        Returns:
            Translation result with narrative and metadata
        """
        if not self.is_configured():
            return {
                "error": "Anthropic provider not configured",
                "suggested_narrative": None,
                "confidence_score": 0,
            }

        try:
            self.logger.debug(f"Calling Anthropic API with model: {self.model}")

            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )

            response_text = response.content[0].text
            result = self._parse_response(response_text)

            self.logger.info(f"Anthropic translation successful")
            return result

        except Exception as e:
            self.logger.error(f"Anthropic API error: {e}")
            return {
                "error": str(e),
                "suggested_narrative": None,
                "confidence_score": 0,
                "format_type": "error",
            }

    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """Parse JSON response from Anthropic."""
        try:
            import json
            import re

            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                parsed = json.loads(json_str)
                return {
                    "suggested_narrative": parsed.get("suggested_narrative"),
                    "format_type": parsed.get("format_type", "narrative"),
                    "confidence_score": float(parsed.get("confidence_score", 0.5)),
                    "reasoning": parsed.get("reasoning", ""),
                }
            else:
                return {
                    "suggested_narrative": response_text,
                    "format_type": "narrative",
                    "confidence_score": 0.3,
                    "reasoning": "Response did not contain JSON",
                }
        except Exception as e:
            self.logger.warning(f"Error parsing Anthropic response: {e}")
            return {
                "suggested_narrative": response_text,
                "format_type": "narrative",
                "confidence_score": 0.2,
            }


class OpenAIProvider(LLMProvider):
    """OpenAI GPT API provider."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4-turbo"):
        """
        Initialize OpenAI provider.

        Args:
            api_key: OpenAI API key
            model: Model name to use (default: gpt-4-turbo)
        """
        self.api_key = api_key
        self.model = model
        self.logger = logger

        if self.api_key:
            try:
                from openai import OpenAI

                self.client = OpenAI(api_key=self.api_key)
                self.logger.info("OpenAI provider initialized successfully")
            except ImportError:
                self.logger.error("openai package not installed. Install with: pip install openai")
                self.client = None
            except Exception as e:
                self.logger.error(f"Failed to initialize OpenAI client: {e}")
                self.client = None
        else:
            self.client = None

    def is_configured(self) -> bool:
        """Check if OpenAI provider is configured."""
        return self.client is not None and self.api_key is not None

    def get_provider_name(self) -> str:
        """Get provider name."""
        return "OpenAI"

    def translate_change(
        self,
        change_data: Dict[str, Any],
        context: str,
        system_prompt: str,
        user_prompt: str,
    ) -> Dict[str, Any]:
        """
        Translate change using OpenAI GPT API.

        Args:
            change_data: Change data dictionary
            context: Additional context
            system_prompt: System prompt
            user_prompt: User prompt

        Returns:
            Translation result with narrative and metadata
        """
        if not self.is_configured():
            return {
                "error": "OpenAI provider not configured",
                "suggested_narrative": None,
                "confidence_score": 0,
            }

        try:
            self.logger.debug(f"Calling OpenAI API with model: {self.model}")

            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=1000,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )

            response_text = response.choices[0].message.content
            result = self._parse_response(response_text)

            self.logger.info(f"OpenAI translation successful")
            return result

        except Exception as e:
            self.logger.error(f"OpenAI API error: {e}")
            return {
                "error": str(e),
                "suggested_narrative": None,
                "confidence_score": 0,
                "format_type": "error",
            }

    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """Parse JSON response from OpenAI."""
        try:
            import json
            import re

            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                parsed = json.loads(json_str)
                return {
                    "suggested_narrative": parsed.get("suggested_narrative"),
                    "format_type": parsed.get("format_type", "narrative"),
                    "confidence_score": float(parsed.get("confidence_score", 0.5)),
                    "reasoning": parsed.get("reasoning", ""),
                }
            else:
                return {
                    "suggested_narrative": response_text,
                    "format_type": "narrative",
                    "confidence_score": 0.3,
                    "reasoning": "Response did not contain JSON",
                }
        except Exception as e:
            self.logger.warning(f"Error parsing OpenAI response: {e}")
            return {
                "suggested_narrative": response_text,
                "format_type": "narrative",
                "confidence_score": 0.2,
            }


class MockProvider(LLMProvider):
    """Mock LLM provider for testing without API key."""

    def __init__(self):
        """Initialize mock provider."""
        self.logger = logger

    def is_configured(self) -> bool:
        """Mock provider is always available."""
        return True

    def get_provider_name(self) -> str:
        """Get provider name."""
        return "Mock (No API)"

    def translate_change(
        self,
        change_data: Dict[str, Any],
        context: str,
        system_prompt: str,
        user_prompt: str,
    ) -> Dict[str, Any]:
        """
        Generate mock translation without calling any API.

        Args:
            change_data: Change data dictionary
            context: Additional context
            system_prompt: System prompt (ignored in mock)
            user_prompt: User prompt (ignored in mock)

        Returns:
            Mock translation result
        """
        try:
            original = change_data.get("original_data", {})
            section_name = original.get("Section_Name", "Policy Section")
            new_value = original.get("Policy_Content", "")
            change_type = change_data.get("match_details", {}).get("section_title", section_name)

            # Generate reasonable mock narrative
            mock_narrative = self._generate_mock_narrative(
                section_name, new_value, original.get("Change_Type", "Modified")
            )

            self.logger.info(
                f"Mock translation generated for {section_name} "
                "(Note: This is a mock without real LLM)"
            )

            return {
                "suggested_narrative": mock_narrative,
                "format_type": "narrative",
                "confidence_score": 0.5,  # Lower confidence for mock
                "reasoning": "Generated by mock provider (no LLM API). Please review carefully.",
                "is_mock": True,
            }

        except Exception as e:
            self.logger.error(f"Mock provider error: {e}")
            return {
                "suggested_narrative": None,
                "format_type": "error",
                "confidence_score": 0,
                "error": str(e),
            }

    def _generate_mock_narrative(
        self, section_name: str, content: str, change_type: str
    ) -> str:
        """Generate a mock narrative for testing."""
        if change_type == "NEW":
            return f"New section added: {section_name}. {content}"
        elif change_type == "MODIFIED":
            return f"Section {section_name} has been updated. The updated content is: {content}"
        elif change_type == "DELETED":
            return f"Section {section_name} has been removed from the policy."
        else:
            return f"Policy section {section_name}: {content}"


class LLMProviderFactory:
    """Factory for creating LLM providers."""

    @staticmethod
    def create_provider(
        provider_type: str = "anthropic",
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ) -> LLMProvider:
        """
        Create an LLM provider instance.

        Args:
            provider_type: Type of provider ('anthropic', 'openai', 'mock')
            api_key: API key for the provider
            model: Model name to use

        Returns:
            LLMProvider instance
        """
        provider_type = provider_type.lower()

        logger.info(f"Creating LLM provider: {provider_type}")

        if provider_type == "anthropic":
            return AnthropicProvider(
                api_key=api_key,
                model=model or "claude-3-5-sonnet-20241022",
            )
        elif provider_type == "openai":
            return OpenAIProvider(
                api_key=api_key,
                model=model or "gpt-4-turbo",
            )
        elif provider_type == "mock":
            logger.warning("Using Mock LLM provider (no API calls, testing only)")
            return MockProvider()
        else:
            logger.warning(f"Unknown provider type '{provider_type}', using mock provider")
            return MockProvider()

    @staticmethod
    def get_available_providers() -> Dict[str, str]:
        """Get list of available providers."""
        return {
            "anthropic": "Anthropic Claude API",
            "openai": "OpenAI GPT API",
            "mock": "Mock Provider (Testing only, no API required)",
        }
