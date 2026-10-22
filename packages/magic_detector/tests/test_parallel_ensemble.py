"""Unit tests for parallel execution and ensemble strategies."""

import pytest

from magic_detector import (
    CompositeEnsembleStrategy,
    InputTarget,
    MagicBytesChecker,
    MagicEncodingChecker,
    MagicExtensionChecker,
    MagicMimeChecker,
    ConsensusEnsembleStrategy,
    ConsensusMode,
    ParallelRunner,
    FirstMatchEnsembleStrategy,
    MagicDetectorSuite,
)


def test_parallel_composite_ensemble():
    runner = ParallelRunner(
        checkers=[
            MagicMimeChecker(),
            MagicBytesChecker(),
            MagicEncodingChecker(),
            MagicExtensionChecker(),
        ],
        ensemble_strategy=CompositeEnsembleStrategy(),
        max_workers=4,
    )

    target = InputTarget(buffer=b"\x89PNG\r\n\x1a\n", file_name="image.png")
    res = runner.run(target)

    assert res.mime_type == "image/png"
    assert res.extension == "png"
    assert res.checker_name == "ensemble_composite"
    assert len(res.details["all_results"]) == 4


def test_parallel_first_match_ensemble():
    runner = ParallelRunner(
        checkers=[
            MagicMimeChecker(),
            MagicBytesChecker(),
        ],
        ensemble_strategy=FirstMatchEnsembleStrategy(),
    )

    target = InputTarget(buffer=b"%PDF-1.4")
    res = runner.run(target)

    assert res.mime_type == "application/pdf"
    assert "ensemble_first_match" in res.checker_name


def test_parallel_majority_vote_ensemble():
    runner = ParallelRunner(
        checkers=[
            MagicMimeChecker(name="m1"),
            MagicMimeChecker(name="m2"),
            MagicBytesChecker(name="b1"),
        ],
        ensemble_strategy=ConsensusEnsembleStrategy(mode=ConsensusMode.MAJORITY),
    )

    target = InputTarget(buffer=b"\x89PNG\r\n\x1a\n")
    res = runner.run(target)

    assert res.mime_type == "image/png"
    assert res.checker_name == "ensemble_consensus_majority"
    assert res.details["consensus_reached"] is True


@pytest.mark.anyio
async def test_parallel_runner_async():
    runner = ParallelRunner(
        checkers=[
            MagicMimeChecker(),
            MagicEncodingChecker(),
        ],
        ensemble_strategy=CompositeEnsembleStrategy(),
    )

    target = InputTarget(buffer=b"Hello World text file")
    res = await runner.run_async(target)

    assert res.checker_name == "ensemble_composite"
    assert res.execution_time_ms > 0


import pytest


@pytest.mark.anyio
async def test_detect_normalized_async_batch():
    suite = MagicDetectorSuite()
    batch_res = await suite.detect_normalized_async([b"import os\n", "script.py"], use_parallel=True)
    assert len(batch_res) == 2
    assert batch_res[0].mime_type is not None
