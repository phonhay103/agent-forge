"""Unit tests for sequential pipeline execution engine."""

from magic_detector import (
    FallbackChainStrategy,
    InputTarget,
    MagicBytesChecker,
    MagicEncodingChecker,
    MagicExtensionChecker,
    MagicMimeChecker,
    PipelineRunner,
    SequentialAccumulatorStrategy,
)


def test_pipeline_accumulator():
    runner = PipelineRunner(
        checkers=[
            MagicMimeChecker(),
            MagicBytesChecker(),
            MagicEncodingChecker(),
            MagicExtensionChecker(),
        ],
        strategy=SequentialAccumulatorStrategy(),
    )

    target = InputTarget(buffer=b"\x89PNG\r\n\x1a\n", file_name="test.png")
    res = runner.run(target)

    assert res.mime_type == "image/png"
    assert res.extension == "png"
    assert res.description is not None
    assert res.encoding is not None
    assert "steps" in res.details
    assert len(res.details["steps"]) == 4


def test_pipeline_fallback_chain():
    runner = PipelineRunner(
        checkers=[
            MagicMimeChecker(),
            MagicBytesChecker(),
        ],
        strategy=FallbackChainStrategy(),
    )

    target = InputTarget(buffer=b"<?xml version='1.0'?><root></root>")
    res = runner.run(target)

    assert res.is_success
    