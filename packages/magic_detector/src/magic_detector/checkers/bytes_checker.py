"""Bytes/Description Checker using python-magic."""

import time

from magic_detector.interfaces import BaseChecker
from magic_detector.magic_wrapper import MagicWrapper
from magic_detector.models import CheckerCategory, DetectionResult, InputTarget


class MagicBytesChecker(BaseChecker):
    """Checker mode: Inspects raw bytes to extract human-readable description via python-magic."""

    def __init__(
        self,
        name: str = "magic_bytes",
        wrapper: MagicWrapper | None = None,
        enabled: bool = True,
        max_bytes: int | None = 4096,
    ) -> None:
        self.name = name
        self.enabled = enabled
        self.category = CheckerCategory.HEURISTIC
        self.wrapper = wrapper or MagicWrapper(mime=False)
        self.max_bytes = max_bytes

    def check(self, target: InputTarget) -> DetectionResult:
        start_time = time.perf_counter()
        try:
            if target.buffer is not None:
                desc = self.wrapper.from_buffer(target.get_bytes(self.max_bytes))
            elif target.file_path:
                desc = self.wrapper.from_file(target.file_path)
            else:
                desc = "empty or unknown"

            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            is_valid = desc != "data" and desc != "empty"

            return DetectionResult(
                description=desc,
                checker_name=self.name,
                checker_category=self.category,
                details={"native_magic": self.wrapper.is_native_available, "raw_description": desc},
                execution_time_ms=elapsed_ms,
            )
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return DetectionResult(
                checker_name=self.name,
                checker_category=self.category,
                details={"error": str(e)},
                execution_time_ms=elapsed_ms,
            )

    async def check_async(self, target: InputTarget) -> DetectionResult:
        return self.check(target)
