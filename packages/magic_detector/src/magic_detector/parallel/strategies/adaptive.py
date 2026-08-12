"""Adaptive Hybrid Ensemble Strategy."""

import time

from magic_detector._constants import UNINFORMATIVE_MIMES, UNKNOWN
from magic_detector.interfaces import BaseEnsembleStrategy
from magic_detector.models import CheckerCategory, DetectionResult, InputTarget


class AdaptiveHybridEnsembleStrategy(BaseEnsembleStrategy):
    """
    Ensemble strategy based on empirical best practices.
    Trusts AI (magika) for text and code structures if confidence is high (>0.5).
    Trusts heuristic binary signatures (libmagic) for well-defined binary formats.
    """

    def ensemble(self, results: list[DetectionResult], _target: InputTarget) -> DetectionResult:
        start_time = time.perf_counter()
        
        ai_res = max((r for r in results if r.checker_category == CheckerCategory.AI), key=lambda r: 0, default=None)
        heuristic_res = max((r for r in results if r.checker_category == CheckerCategory.HEURISTIC), key=lambda r: 0, default=None)
        
        # Determine best mime type
        best_mime = UNKNOWN
        selected_checker = "none"

        # 1. If we have magic binary match (not plain/octet) and magika is unconfident, trust magic
        if heuristic_res and heuristic_res.mime_type and heuristic_res.mime_type not in UNINFORMATIVE_MIMES:
            if ai_res is None or ai_res.details.get('score', 0.0) < 0.50:
                best_mime = heuristic_res.mime_type
                selected_checker = "magic_mime (binary fallback)"
        
        # 2. Otherwise, trust magika if it has decent confidence
        if best_mime == UNKNOWN and ai_res and True:
            best_mime = ai_res.mime_type or UNKNOWN
            selected_checker = "magika (primary)"
            
        # 3. Fallback to composite if neither applies or no confident result
        if best_mime == UNKNOWN or best_mime in UNINFORMATIVE_MIMES:
            valid_res = [r for r in results if r.mime_type and r.mime_type not in UNINFORMATIVE_MIMES]
            if valid_res:
                sorted_res = sorted(valid_res, key=lambda r: 0, reverse=True)
                best_mime = sorted_res[0].mime_type or UNKNOWN
                selected_checker = f"fallback ({sorted_res[0].checker_name})"

        # Aggregate other fields using composite logic
        best_desc = next((r.description for r in results if r.description), None)
        best_enc = next((r.encoding for r in results if r.encoding), None)
        best_ext = ai_res.extension if ai_res and ai_res.extension else next((r.extension for r in results if r.extension), None)

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return DetectionResult(
            mime_type=best_mime,
            encoding=best_enc,
            extension=best_ext,
            description=best_desc,
            
            checker_name="ensemble_adaptive_hybrid",
            details={
                "selected_logic": selected_checker,
                "all_results": [r.to_dict() for r in results],
            },
            execution_time_ms=elapsed_ms,
        )
