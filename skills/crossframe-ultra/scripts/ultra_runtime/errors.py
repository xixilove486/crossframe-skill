from __future__ import annotations


class UltraRuntimeError(Exception):
    """Base exception for deterministic CrossFrame Ultra runtime failures."""


class UltraSchemaError(UltraRuntimeError):
    """Raised when an Ultra schema resource cannot be loaded safely."""


class UltraCompatibilityError(UltraRuntimeError):
    """Raised when a compatibility or source-promotion request is malformed."""
