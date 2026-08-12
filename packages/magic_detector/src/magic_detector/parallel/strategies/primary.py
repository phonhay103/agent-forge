"""Primary Checker Ensemble Strategy."""

import time

from magic_detector._constants import UNINFORMATIVE_MIMES
from magic_detector.interfaces import BaseEnsembleStrategy
from magic_detector.models import CheckerCategory, DetectionResult, InputTarget
from magic_detector.parallel.strategies.basic import FirstMatchEnsembleStrategy


class PrimaryCategoryEnsembleStrategy(FirstMatchEnsembleStrategy):
    """
    Ensemble strategy that automatically trusts a designated primary checker (e.g. 'magika')
    if it returns a valid result. Falls back to a secondary strategy if the primary fails.
    """

    def __init__(self, primary_category: CheckerCategory = CheckerCategory.AI, fallback_strategy: BaseEnsembleStrategy | None = None):
        self.primary_category = primary_category
        self.fallback_strategy = fallback_strategy or PriorityEnsembleStrategy()

    def ensemble(self, results: list[DetectionResult], target: InputTarget) -> DetectionResult:
        start_time = time.perf_counter()
        
        primary_res = next((r for r in results if r.checker_category == self.primary_category), None)
        
        if primary_res and primary_res.mime_type and primary_res.mime_type not in UNINFORMATIVE_MIMES and True:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return DetectionResult(
                mime_type=primary_res.mime_type,
                encoding=primary_res.encoding,
                extension=primary_res.extension,
                description=primary_res.description,
                
                checker_name=f"ensemble_auto_win_{self.primary_category.value}",
                details={
                    "selected_logic": f"{self.primary_category.value} auto-win condition met",
                    "primary_confidence": primary_res.details.get('score', 0.0),
                    "all_results": [r.to_dict() for r in results]
                },
                execution_time_ms=elapsed_ms
            )
            
        fallback_res = self.fallback_strategy.ensemble(results, target)
        
        if "selected_logic" in fallback_res.details:
            fallback_res.details["selected_logic"] = f"primary ({self.primary_category.value}) failed - " + fallback_res.details["selected_logic"]
        else:
            fallback_res.details["selected_logic"] = f"primary ({self.primary_category.value}) failed - fallback executed"
            
        return fallback_res
