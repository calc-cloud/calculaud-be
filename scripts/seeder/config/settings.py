"""Configuration settings for the seeding system."""

import json
from pathlib import Path
from typing import Any

# Base paths
SEEDER_ROOT = Path(__file__).parent.parent
CONFIG_DATA_DIR = SEEDER_ROOT / "config" / "data"


class SeedingConfig:
    """Configuration class for seeding operations."""

    # Default quantities for mock data generation
    DEFAULT_PURPOSE_COUNT = 40
    DEFAULT_BATCH_SIZE = 1000

    # Random data generation settings
    RANDOM_SEED = 42  # For reproducible results

    # Date ranges for random generation (years ago)
    PURPOSE_CREATION_YEARS_AGO = 3
    PURPOSE_DELIVERY_YEARS_FUTURE = 1
    STAGE_COMPLETION_YEARS_AGO = 2

    @classmethod
    def load_json_data(cls, filename: str) -> Any:
        """
        Load JSON data from the config/data directory.

        Args:
            filename: Name of the JSON file (with or without .json extension)

        Returns:
            Parsed JSON data

        Raises:
            FileNotFoundError: If the file doesn't exist
            json.JSONDecodeError: If the file contains invalid JSON
        """
        if not filename.endswith(".json"):
            filename += ".json"

        file_path = CONFIG_DATA_DIR / filename

        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    @classmethod
    def get_responsible_authorities(cls) -> list[dict[str, str]]:
        """Load responsible authorities data."""
        return cls.load_json_data("responsible_authorities.json")

    @classmethod
    def get_budget_sources(cls) -> list[dict[str, str]]:
        """Load budget sources data."""
        return cls.load_json_data("budget_sources.json")

    @classmethod
    def get_service_types(cls) -> dict[str, list[str]]:
        """Load service types and their associated services."""
        return cls.load_json_data("service_types.json")

    @classmethod
    def get_suppliers(cls) -> list[str]:
        """Load suppliers list."""
        return cls.load_json_data("suppliers.json")

    @classmethod
    def get_stage_flows(cls) -> dict[str, Any]:
        """Load stage types and predefined flows configuration."""
        return cls.load_json_data("stage_flows.json")

    @classmethod
    def get_purpose_descriptions(cls) -> list[str]:
        """Load purpose descriptions from JSON file."""
        return cls.load_json_data("purpose_descriptions.json")

    @classmethod
    def get_hierarchy_backup_data(cls) -> list[tuple[int, int | None, str, str, str]]:
        """
        Get hierarchy data from backup.

        Returns:
            List of tuples: (id, parent_id, type_str, name, path)
        """
        hierarchy_data = cls.load_json_data("hierarchy_backup.json")
        return [
            (
                item["id"],
                item["parent_id"],
                item["type"],
                item["name"],
                item["path"],
            )
            for item in hierarchy_data
        ]
