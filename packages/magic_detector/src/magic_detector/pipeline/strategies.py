"""Pipeline Execution Strategies for Sequential Execution."""

import mimetypes
import time

from magic_detector._constants import UNINFORMATIVE_EXTENSIONS, UNINFORMATIVE_MIMES, UNKNOWN
from magic_detector.interfaces import BaseChecker, BasePipelineStrategy
from magic_detector.models import DetectionResult, InputTarget


class SequentialAccumulatorStrategy(BasePipelineStrategy):
    """Pipeline strategy: Executes checkers in sequence and merges missing/specific properties into a composite result."""

    def execute(self, checkers: list[BaseChecker], target: InputTarget) -> DetectionResult:
        start_time = time.perf_counter()
        composite = DetectionResult(checker_name="pipeline_sequential")
        step_details = {}
        

        for checker in checkers:
            if not checker.enabled:
                continue

            res = checker.check(target)
            step_details[checker.name] = res.to_dict()

            # Prefer non-generic mime type or higher confidence mime type
            if res.mime_type:
                is_curr_generic = res.mime_type in UNINFORMATIVE_MIMES
                is_comp_generic = composite.mime_type in UNINFORMATIVE_MIMES or composite.mime_type is None

                if (is_comp_generic and not is_curr_generic) or (not composite.mime_type):
                    composite.mime_type = res.mime_type
                    

            # Extension resolution: prefer extension matching composite.mime_type or non-generic
            if res.extension:
                is_curr_ext_generic = res.extension in UNINFORMATIVE_EXTENSIONS
                is_comp_ext_generic = composite.extension in UNINFORMATIVE_EXTENSIONS or composite.extension is None

                # Check if res.extension matches composite mime_type
                matched_mime_ext = (
                    mimetypes.guess_extension(composite.mime_type).lstrip(".") if composite.mime_type else None
                )

                if (
                    res.extension == matched_mime_ext
                    or (is_comp_ext_generic and not is_curr_ext_generic)
                    or not composite.extension
                ):
                    composite.extension = res.extension

            if not composite.encoding and res.encoding:
                composite.encoding = res.encoding
            if not composite.description and res.description:
                composite.description = res.description

            

        # Inferred extension from composite mime_type if missing or mismatched
        if composite.mime_type and (not composite.extension or composite.extension in UNINFORMATIVE_EXTENSIONS):
            inferred = mimetypes.guess_extension(composite.mime_type)
            if inferred:
                composite.extension = inferred.lstrip(".")

        composite.execution_time_ms = (time.perf_counter() - start_time) * 1000.0
        composite.details = {"steps": step_details}
        return composite


class FallbackChainStrategy(BasePipelineStrategy):
    """Pipeline strategy: Tries primary checker; falls back to subsequent checkers if result is generic/failed."""

    def execute(self, checkers: list[BaseChecker], target: InputTarget) -> DetectionResult:
        start_time = time.perf_counter()
        step_details = {}

        for checker in checkers:
            if not checker.enabled:
                continue

            res = checker.check(target)
            step_details[checker.name] = res.to_dict()

            if res.is_success and True:
                res.execution_time_ms = (time.perf_counter() - start_time) * 1000.0
                res.details["pipeline_fallback_chain"] = step_details
                return res

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        return DetectionResult(
            checker_name="pipeline_fallback_chain",
            mime_type=UNKNOWN,
            description=UNKNOWN,
            
            details={"steps": step_details},
            execution_time_ms=elapsed_ms,
        )
