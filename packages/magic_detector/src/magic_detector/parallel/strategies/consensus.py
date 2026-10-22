"""Consensus-based Ensemble Strategy."""

import time
from collections import Counter
from enum import StrEnum
from typing import override

from magic_detector._constants import UNINFORMATIVE_MIMES, UNKNOWN
from magic_detector.interfaces import BaseEnsembleStrategy
from magic_detector.models import DetectionResult, InputTarget


class ConsensusMode(StrEnum):
    """Modes for consensus matching."""

    STRICT = "strict"  # 100% agreement required among valid checkers
    MAJORITY = "majority"  # > 50% agreement required
    RELAXED = "relaxed"  # Plurality wins


class ConsensusEnsembleStrategy(BaseEnsembleStrategy):
    """
    Ensemble strategy that aggregates results based on configurable consensus rules.
    Allows strict mode (all must agree) or relaxed modes (majority/plurality).
    """

    def __init__(self, mode: ConsensusMode | str = ConsensusMode.STRICT) -> None:
        self.mode = ConsensusMode(mode)

    @override
    def ensemble(self, results: list[DetectionResult], target: InputTarget) -> DetectionResult:
        start_time = time.perf_counter()

        valid_results = [r for r in results if r.mime_type and r.mime_type not in UNINFORMATIVE_MIMES and True]

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        if not valid_results:
            return DetectionResult(
                mime_type=UNKNOWN,
                checker_name=f"ensemble_consensus_{self.mode.value}",
                details={"error": "No valid results to reach consensus", "all_results": [r.to_dict() for r in results]},
                execution_time_ms=elapsed_ms,
            )

        mimes = [r.mime_type for r in valid_results]
        counter = Counter(mimes)
        top_mime, top_count = counter.most_common(1)[0]

        agreed = False
        if self.mode == ConsensusMode.STRICT:
            agreed = top_count == len(valid_results)
        elif self.mode == ConsensusMode.MAJORITY:
            agreed = top_count > len(valid_results) / 2
        elif self.mode == ConsensusMode.RELAXED:
            agreed = True

        if agreed:
            best_res = next(r for r in valid_results if r.mime_type == top_mime)
            return DetectionResult(
                mime_type=best_res.mime_type,
                encoding=best_res.encoding,
                extension=best_res.extension,
                description=best_res.description,
                checker_name=f"ensemble_consensus_{self.mode.value}",
                details={
                    "consensus_reached": True,
                    "mode": self.mode.value,
                    "votes": dict(counter),
                    "all_results": [r.to_dict() for r in results],
                },
                execution_time_ms=elapsed_ms,
            )
        else:
            return DetectionResult(
                mime_type=UNKNOWN,
                checker_name=f"ensemble_consensus_{self.mode.value}",
                details={
                    "consensus_reached": False,
                    "mode": self.mode.value,
                    "conflict_detected": True,
                    "votes": dict(counter),
                    "all_results": [r.to_dict() for r in results],
                },
                execution_time_ms=elapsed_ms,
            )
