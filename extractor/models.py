"""Standard data models for scraping operations."""

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class ScrapingResult:
    """Standard result format for scraping operations."""

    url: str
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: Optional[datetime] = None
    duration_ms: Optional[int] = None
    method_used: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = asdict(self)
        if self.timestamp:
            result["timestamp"] = self.timestamp.isoformat()
        return result
