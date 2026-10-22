"""Extension Checker based on file path and MIME type inference."""

import mimetypes
import os
import time
from typing import override

from magic_detector.checkers.mime_checker import MagicMimeChecker
from magic_detector.interfaces import BaseChecker
from magic_detector.models import CheckerCategory, DetectionResult, InputTarget


class MagicExtensionChecker(BaseChecker):
    """Checker mode: Infers file extension using python-magic MIME detection and file path analysis."""

    def __init__(
        self,
        name: str = "magic_extension",
        mime_checker: MagicMimeChecker | None = None,
        enabled: bool = True,
    ) -> None:
        self.name = name
        self.enabled = enabled
        self.category = CheckerCategory.HEURISTIC
        self.mime_checker = mime_checker or MagicMimeChecker()

    @override
    def check(self, target: InputTarget) -> DetectionResult:
        start_time = time.perf_counter()
        inferred_ext = None
        mime_type = None

        # Step 1: Try path extension
        file_ref = target.file_name or target.file_path
        if file_ref:
            _, ext = os.path.splitext(file_ref)
            if ext:
                inferred_ext = ext.lstrip(".").lower()

        # Step 2: Try MIME lookup via MagicMimeChecker
        mime_res = self.mime_checker.check(target)
        mime_type = mime_res.mime_type
        if mime_type:
            mime_ext = mimetypes.guess_extension(mime_type)
            if mime_ext:
                inferred_ext = mime_ext.lstrip(".").lower()

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return DetectionResult(
            extension=inferred_ext,
            mime_type=mime_type,
            checker_name=self.name,
            checker_category=self.category,
            details={
                "path_ref": file_ref,
                "mime_type": mime_type,
                "inferred_extension": inferred_ext,
            },
            execution_time_ms=elapsed_ms,
        )

    @override
    async def check_async(self, target: InputTarget) -> DetectionResult:
        return self.check(target)
