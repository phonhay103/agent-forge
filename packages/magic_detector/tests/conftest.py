"""Pytest configuration and fixtures for magic_detector tests."""

from typing import Any

import pytest

from magic_detector.magic_wrapper import MagicWrapper


class MockMagicInstance:
    """Mock python-magic instance for test environments missing C libmagic."""

    def __init__(
        self,
        mime: bool = False,
        mime_encoding: bool = False,
        uncompress: bool = False,
        magic_file: str | None = None,
        raw: bool = False,
        keep_going: bool = False,
    ) -> None:
        self.mime = mime
        self.mime_encoding = mime_encoding
        self.uncompress = uncompress
        self.raw = raw
        self.magic_file = magic_file
        self.keep_going = keep_going

    def from_buffer(self, buffer: bytes) -> str:
        if self.mime_encoding:
            if buffer.isascii():
                return "us-ascii"
            return "utf-8"
        if self.mime:
            if buffer.startswith(b"\x89PNG"):
                return "image/png"
            if buffer.startswith(b"%PDF"):
                return "application/pdf"
            if buffer.startswith(b"PK\x03\x04"):
                return "application/zip"
            return "text/plain"

        if buffer.startswith(b"%PDF"):
            return "PDF document, version 1.4"
        if buffer.startswith(b"\x89PNG"):
            return "PNG image data"
        if buffer.startswith(b"PK\x03\x04"):
            return "Zip archive data"
        return "ASCII text"

    def from_file(self, file_path: str) -> str:
        with open(file_path, "rb") as f:
            return self.from_buffer(f.read())


@pytest.fixture(autouse=True)
def mock_magic_wrapper_if_needed(monkeypatch: pytest.MonkeyPatch) -> None:
    """Automatically inject mock python-magic instance in tests if libmagic C library is not loaded."""
    test_wrapper = MagicWrapper()
    if not test_wrapper.is_native_available:
        original_init = MagicWrapper.__init__

        def mocked_init(self: MagicWrapper, magic_instance: Any | None = None, **kwargs: Any) -> None:
            if magic_instance is None:
                magic_instance = MockMagicInstance(**kwargs)
            original_init(self, magic_instance=magic_instance, **kwargs)

        monkeypatch.setattr(MagicWrapper, "__init__", mocked_init)
