"""Unit tests for MagikaChecker and hybrid Magika + Python-Magic integration."""

from magic_detector import (
    InputTarget,
    MagicDetectorSuite,
    MagikaChecker,
)


def test_magika_checker_standalone():
    checker = MagikaChecker()
    python_code = b"import sys\nimport os\nprint('hello')\n"
    res = checker.check(InputTarget(buffer=python_code))

    assert res.checker_name == "magika"
    assert res.mime_type == "text/x-python" or res.extension == "py"
    assert "label" in res.details
    assert res.details["label"] == "python"


def test_magika_client_standalone():
    suite = MagicDetectorSuite()
    res = suite.detect_magika(b"import os\nimport sys\n")
    assert res.checker_name == "magika"
    

def test_hybrid_pipeline_with_magika():
    suite = MagicDetectorSuite()
    python_code = b"import sys\nimport os\n"
    res = suite.detect_pipeline(python_code, file_name="script.py")

    assert res.mime_type is not None
    assert "magika" in res.details["steps"]
    assert "magic_mime" in res.details["steps"]


def test_hybrid_parallel_ensemble_with_magika():
    suite = MagicDetectorSuite()
    python_code = b"import sys\nimport os\n"
    res = suite.detect_parallel(python_code, file_name="script.py")

    assert res.checker_name == "ensemble_adaptive_hybrid"
    assert res.mime_type is not None
    assert len(res.details["all_results"]) >= 5
