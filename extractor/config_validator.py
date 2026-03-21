"""Extraction configuration validation."""

from typing import Any, Dict


class ConfigValidator:
    """Validate extraction configurations."""

    @staticmethod
    def validate_extract_config(config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize extraction configuration."""
        if not isinstance(config, dict):
            raise ValueError("Extract config must be a dictionary")

        validated_config = {}

        for key, value in config.items():
            if isinstance(value, str):
                # Simple CSS selector
                validated_config[key] = {"selector": value, "multiple": True}
            elif isinstance(value, dict):
                # Complex configuration
                if "selector" not in value:
                    raise ValueError(f"Missing 'selector' for key '{key}'")

                validated_config[key] = {
                    "selector": value["selector"],
                    "attr": value.get("attr", "text"),
                    "multiple": value.get("multiple", False),
                    "type": value.get("type", "css"),
                }
            else:
                raise ValueError(f"Invalid config value for key '{key}'")

        return validated_config
