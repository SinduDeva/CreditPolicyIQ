"""File storage utilities for JSON operations."""
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class FileStorage:
    """Simple file-based JSON storage."""

    def __init__(self, base_dir: str = "data"):
        """
        Initialize file storage.

        Args:
            base_dir: Base directory for storage
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save_json(self, relative_path: str, data: Dict[str, Any]) -> bool:
        """
        Save data to JSON file.

        Args:
            relative_path: Path relative to base_dir
            data: Data to save

        Returns:
            True if successful
        """
        try:
            file_path = self.base_dir / relative_path
            file_path.parent.mkdir(parents=True, exist_ok=True)

            with open(file_path, "w") as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Saved JSON to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving JSON to {relative_path}: {e}")
            return False

    def load_json(self, relative_path: str) -> Optional[Dict[str, Any]]:
        """
        Load data from JSON file.

        Args:
            relative_path: Path relative to base_dir

        Returns:
            Loaded data or None if not found
        """
        try:
            file_path = self.base_dir / relative_path
            if not file_path.exists():
                logger.warning(f"JSON file not found: {file_path}")
                return None

            with open(file_path, "r") as f:
                data = json.load(f)
            logger.debug(f"Loaded JSON from {file_path}")
            return data
        except Exception as e:
            logger.error(f"Error loading JSON from {relative_path}: {e}")
            return None

    def list_files(self, directory: str, pattern: str = "*.json") -> List[str]:
        """
        List files in directory.

        Args:
            directory: Directory relative to base_dir
            pattern: File pattern to match

        Returns:
            List of file names
        """
        try:
            dir_path = self.base_dir / directory
            if not dir_path.exists():
                return []
            return [f.name for f in dir_path.glob(pattern)]
        except Exception as e:
            logger.error(f"Error listing files in {directory}: {e}")
            return []

    def append_to_log(
        self, log_path: str, entry: Dict[str, Any]
    ) -> bool:
        """
        Append entry to JSON log file.

        Args:
            log_path: Path to log file relative to base_dir
            entry: Entry to append

        Returns:
            True if successful
        """
        try:
            file_path = self.base_dir / log_path
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Load existing log or create new
            log_data = {"entries": []}
            if file_path.exists():
                with open(file_path, "r") as f:
                    log_data = json.load(f)

            # Ensure entries is a list
            if not isinstance(log_data.get("entries"), list):
                log_data["entries"] = []

            # Add timestamp to entry
            entry["timestamp"] = datetime.utcnow().isoformat()

            # Append entry
            log_data["entries"].append(entry)

            # Save updated log
            with open(file_path, "w") as f:
                json.dump(log_data, f, indent=2)

            logger.debug(f"Appended entry to log: {log_path}")
            return True
        except Exception as e:
            logger.error(f"Error appending to log {log_path}: {e}")
            return False

    def delete_file(self, relative_path: str) -> bool:
        """
        Delete a file.

        Args:
            relative_path: Path relative to base_dir

        Returns:
            True if successful
        """
        try:
            file_path = self.base_dir / relative_path
            if file_path.exists():
                file_path.unlink()
                logger.debug(f"Deleted file: {file_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting file {relative_path}: {e}")
            return False

    def file_exists(self, relative_path: str) -> bool:
        """
        Check if file exists.

        Args:
            relative_path: Path relative to base_dir

        Returns:
            True if file exists
        """
        file_path = self.base_dir / relative_path
        return file_path.exists()


# Global storage instance
file_storage = FileStorage()
