"""Checkers package export."""

from magic_detector.checkers.bytes_checker import MagicBytesChecker
from magic_detector.checkers.custom_checker import CustomMagicChecker
from magic_detector.checkers.encoding_checker import MagicEncodingChecker
from magic_detector.checkers.extension_checker import MagicExtensionChecker
from magic_detector.checkers.magika_checker import MagikaChecker
from magic_detector.checkers.mime_checker import MagicMimeChecker

__all__ = [
    "CustomMagicChecker",
    "MagicBytesChecker",
    "MagicEncodingChecker",
    "MagicExtensionChecker",
    "MagicMimeChecker",
    "MagikaChecker",
]
