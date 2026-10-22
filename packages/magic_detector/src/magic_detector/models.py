"""Data models for magic_detector package using Pydantic."""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from magic_detector._constants import DEFAULT_BINARY_MIME


class CheckerCategory(StrEnum):
    """Categorization of the underlying detection technique."""

    AI = "ai"
    HEURISTIC = "heuristic"
    METADATA = "metadata"
    GENERAL = "general"
    ENSEMBLE = "ensemble"


class NormalizedResult(BaseModel):
    """Canonical unified result normalized across python-magic and google/magika."""

    label: str
    mime_type: str
    extension: str | None = None
    category: str = "unknown"
    description: str | None = None
    encoding: str | None = None
    is_text: bool = False
    checker_name: str = "unknown"
    raw_details: dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert normalized result to dictionary."""
        return self.model_dump()


class DetectionResult(BaseModel):
    """Standard result returned by any checker, pipeline, or ensemble strategy."""

    mime_type: str | None = None
    encoding: str | None = None
    extension: str | None = None
    description: str | None = None
    checker_name: str = "unknown"
    checker_category: CheckerCategory = CheckerCategory.GENERAL
    details: dict[str, Any] = Field(default_factory=dict)
    execution_time_ms: float = 0.0

    @property
    def is_success(self) -> bool:
        """Returns True if at least one meaningful property was detected."""
        return bool(
            (self.mime_type and self.mime_type != DEFAULT_BINARY_MIME)
            or self.description
            or self.encoding
            or self.extension
        )

    def normalize(self) -> NormalizedResult:
        """Normalize this DetectionResult to a unified NormalizedResult schema."""
        from magic_detector.normalizer import OutputNormalizer

        return OutputNormalizer.normalize(self)

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary."""
        return self.model_dump()


class InputTarget(BaseModel):
    """Target file or bytes buffer to inspect."""

    buffer: bytes | None = None
    file_path: str | None = None
    file_name: str | None = None

    def get_bytes(self, max_bytes: int | None = None) -> bytes:
        """Read bytes from buffer or file."""
        if self.buffer is not None:
            return self.buffer[:max_bytes] if max_bytes else self.buffer
        if self.file_path:
            with open(self.file_path, "rb") as f:
                return f.read(max_bytes) if max_bytes else f.read()
        raise ValueError("InputTarget contains neither buffer nor file_path")
