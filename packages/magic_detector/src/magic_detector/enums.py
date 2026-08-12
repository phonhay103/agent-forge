"""Enums for magic_detector, extending Magika's ContentTypeLabel."""

from enum import StrEnum
from magika import ContentTypeLabel

_magika_members = [(member.name, member.value) for member in ContentTypeLabel]
_magika_names = {name for name, _ in _magika_members}

_custom_members = [
    ("BAML", "baml"),
    ("TOON", "toon"),
    ("HCL", "hcl"),
    ("TOML", "toml"),
    ("MARKDOWN", "markdown"),
    ("UNKNOWN", "unknown"),
]

# Only append custom members if they are not already in magika
_final_members = _magika_members + [m for m in _custom_members if m[0] not in _magika_names]

# Dynamically create FileType Enum by extending Magika's ContentTypeLabel
FileType = StrEnum("FileType", _final_members)
