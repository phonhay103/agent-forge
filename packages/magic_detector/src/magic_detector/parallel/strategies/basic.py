"""Basic ensemble strategies."""

import time
from typing import override

from magic_detector._constants import UNINFORMATIVE_MIMES, UNKNOWN
from magic_detector.interfaces import BaseEnsembleStrategy
from magic_detector.models import DetectionResult, InputTarget


class FirstMatchEnsembleStrategy(BaseEnsembleStrategy):
    """Ensemble strategy: Selects the first result with a non-generic outcome."""

    @override
    def ensemble(self, results: list[DetectionResult], target: InputTarget) -> DetectionResult:
        start_time = time.perf_counter()
        if not results:
            return DetectionResult(checker_name="ensemble_first_match", mime_type=UNKNOWN, description=UNKNOWN)

        # Sort results: non-generic MIME first, preserving original order otherwise
        sorted_res = sorted(
            results,
            key=lambda r: 1 if r.mime_type and r.mime_type not in UNINFORMATIVE_MIMES else 0,
            reverse=True,
        )
        best = sorted_res[0]

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        return DetectionResult(
            mime_type=best.mime_type,
            encoding=best.encoding,
            extension=best.extension,
            description=best.description,
            checker_name=f"ensemble_first_match({best.checker_name})",
            details={
                "selected_checker": best.checker_name,
                "all_results": [r.to_dict() for r in results],
            },
            execution_time_ms=elapsed_ms,
        )


class CompositeEnsembleStrategy(BaseEnsembleStrategy):
    """Ensemble strategy: Combines mime, encoding, extension, and description into a comprehensive result."""

    @override
    def ensemble(self, results: list[DetectionResult], target: InputTarget) -> DetectionResult:
        start_time = time.perf_counter()

        mime_type = None
        encoding = None
        extension = None
        description = None

        for r in results:
            if r.mime_type:
                is_curr_generic = r.mime_type in UNINFORMATIVE_MIMES
                is_comp_generic = mime_type in UNINFORMATIVE_MIMES or mime_type is None

                if (is_comp_generic and not is_curr_generic) or not mime_type:
                    mime_type = r.mime_type

            if not encoding and r.encoding:
                encoding = r.encoding
            if not extension and r.extension:
                extension = r.extension
            if not description and r.description:
                description = r.description

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return DetectionResult(
            mime_type=mime_type,
            encoding=encoding,
            extension=extension,
            description=description,
            checker_name="ensemble_composite",
            details={
                "aggregated_checkers": [r.checker_name for r in results],
                "all_results": [r.to_dict() for r in results],
            },
            execution_time_ms=elapsed_ms,
        )
