"""Data models for Scientific CMS."""

from typing import Dict, Any, Optional
from pydantic import BaseModel


class Document(BaseModel):
    """Represents a parsed CMS document."""
    filename: str
    metadata: Dict[str, Any]
    body: str
    source: str
    compiled_body: Optional[str] = None


class ValidationSettings(BaseModel):
    """Settings for schema validation."""
    mode: str = "warn"  # "off", "warn", "enforce"


class ValidationError(Exception):
    """Exception raised when validation fails."""
    pass