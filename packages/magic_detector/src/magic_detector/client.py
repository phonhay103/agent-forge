"""High-level client suite for python-magic and magika detector system."""

from magic_detector.checkers import (
    CustomMagicChecker,
)
from magic_detector.factory import DetectorContainer, create_default_container
from magic_detector.interfaces import BaseEnsembleStrategy, BasePipelineStrategy
from magic_detector.models import DetectionResult, InputTarget, NormalizedResult


class MagicDetectorSuite:
    """Facade client suite exposing standalone checkers, sequential pipeline execution, and parallel ensemble detection."""

    def __init__(self, container: DetectorContainer | None = None) -> None:
        # DI: Accept optional custom container or create default
        self.container = container or create_default_container()

    # --- Standalone Modes ---

    def detect_magika(self, data: bytes | str) -> DetectionResult:
        """Standalone Mode: Check using Google Magika deep learning model."""
        checker = self.container.get("magika")
        target = InputTarget(buffer=data) if isinstance(data, bytes) else InputTarget(file_path=data)
        return checker.check(target)

    def detect_bytes(self, data: bytes | str) -> DetectionResult:
        """Standalone Mode: Check raw bytes/description using python-magic."""
        self._ensure_magic("magic_bytes")
        checker = self.container.get("magic_bytes")
        target = InputTarget(buffer=data) if isinstance(data, bytes) else InputTarget(file_path=data)
        return checker.check(target)

    def detect_mime(self, data: bytes | str) -> DetectionResult:
        """Standalone Mode: Check MIME type using python-magic."""
        self._ensure_magic("magic_mime")
        checker = self.container.get("magic_mime")
        target = InputTarget(buffer=data) if isinstance(data, bytes) else InputTarget(file_path=data)
        return checker.check(target)

    def detect_encoding(self, data: bytes | str) -> DetectionResult:
        """Standalone Mode: Check encoding/charset using python-magic."""
        self._ensure_magic("magic_encoding")
        checker = self.container.get("magic_encoding")
        target = InputTarget(buffer=data) if isinstance(data, bytes) else InputTarget(file_path=data)
        return checker.check(target)

    def detect_extension(self, data: bytes | str, file_name: str | None = None) -> DetectionResult:
        """Standalone Mode: Check file extension using python-magic and MIME inference."""
        self._ensure_magic("magic_extension")
        checker = self.container.get("magic_extension")
        if isinstance(data, bytes):
            target = InputTarget(buffer=data, file_name=file_name)
        else:
            target = InputTarget(file_path=data, file_name=file_name or data)
        return checker.check(target)

    def detect_custom(
        self,
        data: bytes | str,
        uncompress: bool = False,
        raw: bool = False,
        magic_file: str | None = None,
    ) -> DetectionResult:
        """Standalone Mode: Check using custom python-magic configuration."""
        checker = CustomMagicChecker(uncompress=uncompress, raw=raw, magic_file=magic_file)
        if getattr(checker, "wrapper", None) is not None and checker.wrapper._magic_instance is None:
            raise RuntimeError("python-magic is not installed. Please install magic-detector[magic] to use this feature.")
        target = InputTarget(buffer=data) if isinstance(data, bytes) else InputTarget(file_path=data)
        return checker.check(target)

    def _ensure_magic(self, checker_name: str) -> None:
        try:
            checker = self.container.get(checker_name)
            if getattr(checker, "wrapper", None) is not None and checker.wrapper._magic_instance is None:
                raise RuntimeError("python-magic is not installed. Please install magic-detector[magic] to use this feature.")
        except KeyError:
            pass

    # --- Chained & Normalized Modes ---

    def detect_pipeline(
        self,
        data: bytes | str,
        checker_names: list[str] | None = None,
        strategy: BasePipelineStrategy | None = None,
        file_name: str | None = None,
    ) -> DetectionResult:
        """Pipeline Mode: Execute checkers sequentially step-by-step."""
        target = (
            InputTarget(buffer=data, file_name=file_name)
            if isinstance(data, bytes)
            else InputTarget(file_path=data, file_name=file_name)
        )
        runner = self.container.create_pipeline(checker_names=checker_names, strategy=strategy)
        return runner.run(target)

    def detect_parallel(
        self,
        data: bytes | str,
        checker_names: list[str] | None = None,
        ensemble_strategy: BaseEnsembleStrategy | None = None,
        file_name: str | None = None,
    ) -> DetectionResult:
        """Parallel Mode: Execute checkers concurrently and aggregate via Ensemble strategy."""
        target = (
            InputTarget(buffer=data, file_name=file_name)
            if isinstance(data, bytes)
            else InputTarget(file_path=data, file_name=file_name)
        )
        runner = self.container.create_parallel(checker_names=checker_names, ensemble_strategy=ensemble_strategy)
        return runner.run(target)

    def detect_normalized(
        self,
        data: bytes | str,
        checker_names: list[str] | None = None,
        file_name: str | None = None,
    ) -> NormalizedResult:
        """Normalized Mode: Execute detection pipeline and return a unified NormalizedResult."""
        raw_res = self.detect_pipeline(data, checker_names=checker_names, file_name=file_name)
        return raw_res.normalize()
