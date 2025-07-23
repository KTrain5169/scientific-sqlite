"""Exceptions for Scientific CMS."""


class CMSError(Exception):
    """Base exception for CMS operations."""
    pass


class SchemaValidationError(CMSError):
    """Raised when schema validation fails."""
    pass


class SchemaLoadError(CMSError):
    """Raised when schema loading fails."""
    pass