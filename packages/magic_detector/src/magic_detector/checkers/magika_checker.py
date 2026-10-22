"""Google Magika AI File Type Detector Checker."""

import time
from typing import Any, override

from magika import ContentTypeLabel

from magic_detector._constants import DEFAULT_BINARY_MIME
from magic_detector.interfaces import BaseChecker
from magic_detector.magika_wrapper import MagikaWrapper
from magic_detector.models import CheckerCategory, DetectionResult, InputTarget


class MagikaChecker(BaseChecker):
    """Checker mode: Inspects target using Google Magika deep learning file type model."""

    def __init__(
        self,
        name: str = "magika",
        wrapper: MagikaWrapper | None = None,
        enabled: bool = True,
        max_bytes: int | None = 4096,
        prediction_mode: str = "high_confidence",
    ) -> None:
        self.name = name
        self.enabled = enabled
        self.category = CheckerCategory.AI
        self.max_bytes = max_bytes
        self.wrapper = wrapper or MagikaWrapper(prediction_mode=prediction_mode)

    def _build_result(self, res: Any, elapsed_ms: float) -> DetectionResult:
        # Extract fields safely across Magika versions
        if hasattr(res, "prediction"):
            score = getattr(res.prediction, "score", 0.0)
            output = getattr(res.prediction, "output", None)
        else:
            score = getattr(res, "score", 0.0)
            output = getattr(res, "output", None)

        label = getattr(output, "label", ContentTypeLabel.UNKNOWN) if output else ContentTypeLabel.UNKNOWN
        mime_type = getattr(output, "mime_type", DEFAULT_BINARY_MIME) if output else DEFAULT_BINARY_MIME
        group = getattr(output, "group", "unknown") if output else "unknown"
        description = getattr(output, "description", None) if output else None
        extensions = getattr(output, "extensions", []) if output else []

        primary_ext = extensions[0] if extensions else (label if label != ContentTypeLabel.UNKNOWN else None)

        return DetectionResult(
            mime_type=mime_type,
            extension=primary_ext,
            description=description,
            checker_name=self.name,
            checker_category=self.category,
            details={
                "native_magika": self.wrapper.is_available,
                "label": label,
                "group": group,
                "score": score,
                "extensions": extensions,
            },
            execution_time_ms=elapsed_ms,
        )

    @override
    def check(self, target: InputTarget) -> DetectionResult:
        start_time = time.perf_counter()
        try:
            if target.buffer is not None:
                res = self.wrapper.identify_bytes(target.get_bytes(self.max_bytes))
            elif target.file_path:
                res = self.wrapper.identify_path(target.file_path)
            else:
                res = self.wrapper.identify_bytes(b"")

            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return self._build_result(res, elapsed_ms)
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return DetectionResult(
                checker_name=self.name,
                checker_category=self.category,
                details={"error": str(e)},
                execution_time_ms=elapsed_ms,
            )

    @override
    def check_batch(self, targets: list[InputTarget]) -> list[DetectionResult]:
        """Perform batch check for file paths using Magika's batch capability."""
        start_time = time.perf_counter()

        file_paths: list[str] = []
        target_indices: list[int] = []
        # Placeholders for path targets; buffer targets are checked individually below.
        results: list[DetectionResult | None] = [None] * len(targets)

        for i, target in enumerate(targets):
            if target.file_path and target.buffer is None:
                file_paths.append(target.file_path)
                target_indices.append(i)
            else:
                # If it's a buffer, fall back to individual check
                results[i] = self.check(target)

        if file_paths:
            try:
                magika_results = self.wrapper.identify_paths(file_paths)
                elapsed_ms = (time.perf_counter() - start_time) * 1000.0
                # distribute elapsed time across all items to keep it consistent
                elapsed_ms_per_item = elapsed_ms / len(file_paths)

                for j, res in enumerate(magika_results):
                    idx = target_indices[j]
                    results[idx] = self._build_result(res, elapsed_ms_per_item)

            except Exception as e:
                elapsed_ms = (time.perf_counter() - start_time) * 1000.0
                for idx in target_indices:
                    results[idx] = DetectionResult(
                        checker_name=self.name,
                        checker_category=self.category,
                        details={"error": str(e)},
                        execution_time_ms=elapsed_ms / len(file_paths),
                    )

        # Slots only stay empty if Magika returned fewer results than the paths it was given.
        return [res if res is not None else self.check(target) for res, target in zip(results, targets, strict=True)]

    @override
    async def check_async(self, target: InputTarget) -> DetectionResult:
        return self.check(target)
