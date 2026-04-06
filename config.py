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
        self.api_key = os.getenv("ANTHROPIC_API_KEY", self.config_data.get("api_key", ""))
        self.master_docx = self.config_data.get("master_docx_path", "data/master_policy.docx")
        self.excel_path = self.config_data.get("excel_path", "data/policy_changes.xlsx")
        self.max_tokens = self.config_data.get("max_tokens", 1000)
        self.model = self.config_data.get("model", "claude-3-5-sonnet-20241022")

    def to_dict(self) -> Dict[str, Any]:
        """Return configuration as dictionary."""
        return {
            "api_key": "***" if self.api_key else None,
            "master_docx": self.master_docx,
            "excel_path": self.excel_path,
            "max_tokens": self.max_tokens,
            "model": self.model,
            "data_dir": str(self.data_dir),
        }


# Global config instance
config = Config()
