"""MIME Type Checker using python-magic."""

import time
from typing import override

from magic_detector._constants import DEFAULT_BINARY_MIME
from magic_detector.interfaces import BaseChecker
from magic_detector.magic_wrapper import MagicWrapper
from magic_detector.models import CheckerCategory, DetectionResult, InputTarget


class MagicMimeChecker(BaseChecker):
    """Checker mode: Inspects target to extract MIME type via python-magic."""

    def __init__(
        self,
        name: str = "magic_mime",
        wrapper: MagicWrapper | None = None,
        enabled: bool = True,
        max_bytes: int | None = 4096,
    ) -> None:
        self.name = name
        self.enabled = enabled
        self.category = CheckerCategory.HEURISTIC
        self.wrapper = wrapper or MagicWrapper(mime=True)
        self.max_bytes = max_bytes

    @override
    def check(self, target: InputTarget) -> DetectionResult:
        start_time = time.perf_counter()
        try:
            if target.buffer is not None:
                mime_type = self.wrapper.from_buffer(target.get_bytes(self.max_bytes))
            elif target.file_path:
                mime_type = self.wrapper.from_file(target.file_path)
            else:
                mime_type = DEFAULT_BINARY_MIME

            elapsed_ms = (time.perf_counter() - start_time) * 1000.0

            return DetectionResult(
                mime_type=mime_type,
                checker_name=self.name,
                checker_category=self.category,
                details={"native_magic": self.wrapper.is_native_available, "raw_mime": mime_type},
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

    @override
    async def check_async(self, target: InputTarget) -> DetectionResult:
        return self.check(target)
