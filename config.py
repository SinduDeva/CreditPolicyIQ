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

        # LLM Provider configuration
        self.llm_provider = os.getenv("LLM_PROVIDER", self.config_data.get("llm_provider", "anthropic"))
        self.model = os.getenv(
            "LLM_MODEL",
            self.config_data.get("model", self._get_default_model(self.llm_provider)),
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
        }


# Global config instance
config = Config()
