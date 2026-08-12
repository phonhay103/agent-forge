"""Normalizer engine reusing Magika taxonomy to unify outputs from python-magic and google/magika into a single standardized result."""

import mimetypes
from typing import Any

from magika import ContentTypeLabel, Magika

from magic_detector._constants import DEFAULT_BINARY_MIME
from magic_detector.models import DetectionResult, NormalizedResult

# Lazy-loaded singleton Magika instance to access Magika's built-in 350+ ContentTypeInfo database
_magika_instance: Magika | None = None


def _get_magika_instance() -> Magika:
    global _magika_instance
    if _magika_instance is None:
        _magika_instance = Magika()
    return _magika_instance


class OutputNormalizer:
    """Normalizes detection outputs across different engines reusing Magika's taxonomy and database."""

    @staticmethod
    def normalize(result: DetectionResult) -> NormalizedResult:
        """Convert any DetectionResult into a standardized NormalizedResult using Magika taxonomy."""
        details = result.details or {}
        magika = _get_magika_instance()

        # Extract raw label string
        raw_label: Any = details.get("label")
        label_str: str | None = None

        if hasattr(raw_label, "value"):
            label_str = str(raw_label.value)
        elif raw_label is not None:
            label_str = str(raw_label)

        mime_type = result.mime_type or DEFAULT_BINARY_MIME
        extension = result.extension
        description = result.description or details.get("description")

        # Query Magika database by label or MIME type
        info = None
        if label_str and label_str in magika._cts_infos:
            info = magika._cts_infos[label_str]
        elif mime_type and mime_type != DEFAULT_BINARY_MIME:
            for ct_info in magika._cts_infos.values():
                if ct_info.mime_type == mime_type:
                    info = ct_info
                    break

        if info:
            final_label = info.label
            final_mime = mime_type if mime_type != DEFAULT_BINARY_MIME else info.mime_type
            final_ext = extension or (info.extensions[0] if info.extensions else None)
            final_desc = description or info.description
            category = info.group
            is_text = info.is_text or (
                result.encoding is not None and result.encoding not in ("binary", "unknown")
            )
        else:
            # Fallback for types not in Magika KB
            final_label = label_str or (extension.lower() if extension else ContentTypeLabel.UNKNOWN.value)
            final_mime = mime_type
            final_ext = extension
            if not final_ext and final_mime != DEFAULT_BINARY_MIME:
                guessed = mimetypes.guess_extension(final_mime)
                if guessed:
                    final_ext = guessed.lstrip(".")
            final_desc = description
            category = OutputNormalizer.infer_category_from_mime(final_mime)
            is_text = (
                result.encoding is not None and result.encoding not in ("binary", "unknown")
            ) or final_mime.startswith("text/")

        return NormalizedResult(
            label=str(final_label),
            mime_type=final_mime,
            extension=final_ext,
            category=category,
            description=final_desc,
            encoding=result.encoding,
            is_text=is_text,
            
            checker_name=result.checker_name,
            raw_details=details,
        )

    @staticmethod
    def infer_category_from_mime(mime_type: str) -> str:
        """Infer FileCategory from MIME prefix for types outside Magika KB."""
        if mime_type.startswith("image/"):
            return "image"
        if mime_type.startswith("audio/"):
            return "audio"
        if mime_type.startswith("video/"):
            return "video"
        if mime_type.startswith("font/"):
            return "font"
        if mime_type.startswith("text/"):
            return "text"
        return "unknown"
