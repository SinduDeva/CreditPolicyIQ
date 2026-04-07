"""Configuration management for CreditPolicyIQ."""
import os
import json
from typing import Dict, Any, Optional
from pathlib import Path


class Config:
    """Central configuration management."""

    def __init__(self, config_file: Optional[str] = None):
        """Initialize configuration from file or environment."""
        self.config_data: Dict[str, Any] = {}
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)

        # Load from config file if provided
        if config_file and os.path.exists(config_file):
            with open(config_file, "r") as f:
                self.config_data = json.load(f)

        # Load from environment variables
        # Support both ANTHROPIC_API_KEY and generic LLM_API_KEY
        self.api_key = os.getenv(
            "LLM_API_KEY",
            os.getenv("ANTHROPIC_API_KEY", self.config_data.get("api_key", "")),
        )
        self.master_docx = self.config_data.get("master_docx_path", "data/master_policy.docx")
        self.excel_path = self.config_data.get("excel_path", "data/policy_changes.xlsx")
        self.max_tokens = self.config_data.get("max_tokens", 1000)

        # LLM Provider configuration (defaults to mock for API-free operation)
        self.llm_provider = os.getenv("LLM_PROVIDER", self.config_data.get("llm_provider", "mock"))
        self.model = os.getenv(
            "LLM_MODEL",
            self.config_data.get("model", self._get_default_model(self.llm_provider)),
        )

        # Change detection colors configuration
        # YELLOW: Changes (additions, modifications)
        # GREY: Deletions
        # Set to empty list to detect all colors
        self.highlight_colors = {
            "YELLOW": [
                "FFFF00",  # Pure yellow
                "FFFF99",  # Light yellow
                "FFFF66",  # Light yellow variant
                "FFFF33",  # Medium yellow
                "FFFFCC",  # Cream/light yellow
                "F4D03F",  # Highlight yellow
                "F9E79F",  # Light highlight
                "FEF5E7",  # Very light yellow
            ],
            "GREY": [
                "808080", "7F7F7F", "A9A9A9", "D3D3D3",
                "C0C0C0", "E8E8E8", "696969", "BEBEBE",
            ]
        }

        # Override from config file or environment
        if "highlight_colors" in self.config_data:
            self.highlight_colors = self.config_data["highlight_colors"]

        # Change detection mode: 'yellow_only', 'all_colors', 'configurable'
        self.change_detection_mode = os.getenv(
            "CHANGE_DETECTION_MODE",
            self.config_data.get("change_detection_mode", "yellow_only")
        )

    def _get_default_model(self, provider: str) -> str:
        """Get default model for a given provider."""
        defaults = {
            "anthropic": "claude-3-5-sonnet-20241022",
            "openai": "gpt-4-turbo",
            "mock": "mock",
        }
        return defaults.get(provider.lower(), "claude-3-5-sonnet-20241022")

    def to_dict(self) -> Dict[str, Any]:
        """Return configuration as dictionary."""
        return {
            "llm_provider": self.llm_provider,
            "model": self.model,
            "api_key": "***" if self.api_key else "(not configured)",
            "master_docx": self.master_docx,
            "excel_path": self.excel_path,
            "max_tokens": self.max_tokens,
            "data_dir": str(self.data_dir),
            "change_detection_mode": self.change_detection_mode,
            "highlight_colors": {k: len(v) for k, v in self.highlight_colors.items()},
        }


# Global config instance
config = Config()
