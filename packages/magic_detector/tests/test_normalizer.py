"""Unit tests for OutputNormalizer engine and NormalizedResult."""

from magic_detector import (
    InputTarget,
    MagicDetectorSuite,
    MagikaChecker,
    NormalizedResult,
    OutputNormalizer,
)
from magic_detector.models import DetectionResult


def test_normalize_magika_result():
    python_code = b"import sys\nimport os\nprint('hello')\n"
    checker = MagikaChecker()
    raw_res = checker.check(InputTarget(buffer=python_code))

    norm_res = OutputNormalizer.normalize(raw_res)

    assert isinstance(norm_res, NormalizedResult)
    assert norm_res.label == "python"
    assert norm_res.mime_type == "text/x-python"
    assert norm_res.extension in ("py", "python")
    assert norm_res.category == "code"
    assert norm_res.is_text is True


def test_normalize_detection_result_method():
    raw_res = DetectionResult(
        mime_type="image/png",
        description="PNG image data, 100 x 100",
        extension="png",
        checker_name="magic_mime",
    )

    norm_res = raw_res.normalize()

    assert norm_res.label == "png"
    assert norm_res.mime_type == "image/png"
    assert norm_res.extension == "png"
    assert norm_res.category == "image"
    assert norm_res.is_text is False


def test_suite_detect_normalized():
    suite = MagicDetectorSuite()
    python_code = b"import os\nimport sys\n"

    norm_res = suite.detect_normalized(python_code, file_name="script.py")

    assert isinstance(norm_res, NormalizedResult)
    assert norm_res.label == "python"
    assert norm_res.category == "code"
    assert norm_res.is_text is True
    assert norm_res.to_dict()["mime_type"] == "text/x-python"
