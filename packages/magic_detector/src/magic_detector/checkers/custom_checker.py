"""Custom Parameter Checker using python-magic with advanced flags."""

import time

from magic_detector.interfaces import BaseChecker
from magic_detector.magic_wrapper import MagicWrapper
from magic_detector.models import CheckerCategory, DetectionResult, InputTarget


class CustomMagicChecker(BaseChecker):
    """Checker mode: Flexible python-magic checker supporting custom flags (uncompress, raw, magic_file)."""

    def __init__(
        self,
        name: str = "custom_magic",
        mime: bool = False,
        mime_encoding: bool = False,
        uncompress: bool = False,
        magic_file: str | None = None,
        raw: bool = False,
        keep_going: bool = False,
        wrapper: MagicWrapper | None = None,
        enabled: bool = True,
        max_bytes: int | None = 4096,
    ) -> None:
        self.name = name
        self.enabled = enabled
        self.category = CheckerCategory.HEURISTIC
        self.wrapper = wrapper or MagicWrapper(
            mime=mime,
            mime_encoding=mime_encoding,
            uncompress=uncompress,
            magic_file=magic_file,
            raw=raw,
            keep_going=keep_going,
        )
        self.max_bytes = max_bytes
        self.mime = mime
        self.mime_encoding = mime_encoding

    def check(self, target: InputTarget) -> DetectionResult:
        start_time = time.perf_counter()
        try:
            if target.buffer is not None:
                output = self.wrapper.from_buffer(target.get_bytes(self.max_bytes))
            elif target.file_path:
                output = self.wrapper.from_file(target.file_path)
            else:
                output = "empty or unknown"

            elapsed_ms = (time.perf_counter() - start_time) * 1000.0

            result = DetectionResult(
                checker_name=self.name,
                checker_category=self.category,
                details={
                    "native_magic": self.wrapper.is_native_available,
                    "output": output,
                    "uncompress": self.wrapper.uncompress,
                    "raw": self.wrapper.raw,
                    "magic_file": self.wrapper.magic_file,
                },
                execution_time_ms=elapsed_ms,
            )

            if self.mime:
                result.mime_type = output
            elif self.mime_encoding:
                result.encoding = output
            else:
                result.description = output

            return result
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
