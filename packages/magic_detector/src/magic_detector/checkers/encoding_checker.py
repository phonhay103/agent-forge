"""Encoding / Charset Checker using python-magic."""

import time
from typing import override

from magic_detector.interfaces import BaseChecker
from magic_detector.magic_wrapper import MagicWrapper
from magic_detector.models import CheckerCategory, DetectionResult, InputTarget


class MagicEncodingChecker(BaseChecker):
    """Checker mode: Inspects target to extract text encoding/charset via python-magic."""

    def __init__(
        self,
        name: str = "magic_encoding",
        wrapper: MagicWrapper | None = None,
        enabled: bool = True,
        max_bytes: int | None = 4096,
    ) -> None:
        self.name = name
        self.enabled = enabled
        self.category = CheckerCategory.HEURISTIC
        self.wrapper = wrapper or MagicWrapper(mime_encoding=True)
        self.max_bytes = max_bytes

    @override
    def check(self, target: InputTarget) -> DetectionResult:
        start_time = time.perf_counter()
        try:
            if target.buffer is not None:
                encoding = self.wrapper.from_buffer(target.get_bytes(self.max_bytes))
            elif target.file_path:
                encoding = self.wrapper.from_file(target.file_path)
            else:
                encoding = "binary"

            elapsed_ms = (time.perf_counter() - start_time) * 1000.0

            return DetectionResult(
                encoding=encoding,
                checker_name=self.name,
                checker_category=self.category,
                details={"native_magic": self.wrapper.is_native_available, "raw_encoding": encoding},
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
