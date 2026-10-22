"""Unit tests for MagicDetectorSuite facade and DetectorContainer DI."""

from magic_detector import (
    DetectorContainer,
    MagicBytesChecker,
    MagicDetectorSuite,
    MagicMimeChecker,
)


def test_client_standalone_calls():
    suite = MagicDetectorSuite()

    res_mime = suite.detect_mime(b"\x89PNG\r\n\x1a\n")
    assert res_mime.mime_type == "image/png"

    res_bytes = suite.detect_bytes(b"%PDF-1.4")
    assert res_bytes.description is not None

    res_enc = suite.detect_encoding(b"Hello world\n")
    assert res_enc.encoding is not None

    res_ext = suite.detect_extension(b"\x89PNG\r\n\x1a\n", file_name="photo.png")
    assert res_ext.extension == "png"


def test_client_pipeline_call():
    suite = MagicDetectorSuite()
    res = suite.detect_pipeline(b"%PDF-1.4", file_name="doc.pdf")
    assert res.mime_type == "application/pdf"
    assert res.extension == "pdf"


def test_client_parallel_call():
    suite = MagicDetectorSuite()
    res = suite.detect_parallel(b"\x89PNG\r\n\x1a\n", file_name="pic.png")
    assert res.mime_type == "image/png"
    assert res.extension == "png"


def test_custom_container_di():
    container = DetectorContainer()
    container.register(
        MagicMimeChecker(
            name="custom_mime_1",
        )
    )
    container.register(
        MagicBytesChecker(
            name="custom_bytes_1",
        )
    )

    suite = MagicDetectorSuite(container=container)
    assert suite.container.list_checkers() == ["custom_mime_1", "custom_bytes_1"]

    res = suite.detect_pipeline(b"\x89PNG\r\n\x1a\n")
    assert res.mime_type == "image/png"
