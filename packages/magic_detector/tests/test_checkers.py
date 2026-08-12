"""Unit tests for individual standalone checkers."""

from magika import ContentTypeLabel as MagikaContentTypeLabel

from magic_detector import (
    ContentTypeLabel,
    CustomMagicChecker,
    InputTarget,
    MagicBytesChecker,
    MagicEncodingChecker,
    MagicExtensionChecker,
    MagicMimeChecker,
)


def test_mime_checker_bytes():
    checker = MagicMimeChecker()
    target = InputTarget(buffer=b"\x89PNG\r\n\x1a\n")
    res = checker.check(target)
    assert res.mime_type == "image/png"
    assert res.checker_name == "magic_mime"
    

def test_bytes_checker():
    checker = MagicBytesChecker()
    target = InputTarget(buffer=b"%PDF-1.4 sample content")
    res = checker.check(target)
    assert res.description is not None
    assert "PDF" in res.description or "pdf" in res.description.lower()
    assert res.checker_name == "magic_bytes"


def test_encoding_checker():
    checker = MagicEncodingChecker()
    target = InputTarget(buffer=b"Hello World ascii content\n")
    res = checker.check(target)
    assert res.encoding is not None
    assert res.checker_name == "magic_encoding"


def test_extension_checker():
    checker = MagicExtensionChecker()
    target = InputTarget(buffer=b"\x89PNG\r\n\x1a\n", file_name="image.png")
    res = checker.check(target)
    assert res.extension == "png"
    assert res.checker_name == "magic_extension"


def test_custom_checker():
    checker = CustomMagicChecker(mime=True, uncompress=True)
    target = InputTarget(buffer=b"PK\x03\x04zipcontent")
    res = checker.check(target)
    assert res.mime_type is not None
    assert res.checker_name == "custom_magic"


def test_content_type_label_reexport():
    assert ContentTypeLabel is MagikaContentTypeLabel
    assert ContentTypeLabel.PYTHON == "python"
    assert ContentTypeLabel.PNG == "png"

