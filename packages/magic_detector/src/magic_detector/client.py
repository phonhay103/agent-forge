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

    def detect_magika_paths(self, paths: list[str]) -> list[DetectionResult]:
        """Standalone Mode: Batch check multiple file paths using Google Magika deep learning model."""
        checker = self.container.get("magika")
        targets = [InputTarget(file_path=p) for p in paths]
        if hasattr(checker, "check_paths"):
            return checker.check_paths(targets)
        # Fallback if checker doesn't support batch processing natively
        return [checker.check(t) for t in targets]

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
        data: bytes | str | list[bytes | str],
        checker_names: list[str] | None = None,
        strategy: BasePipelineStrategy | None = None,
        file_name: str | list[str] | None = None,
    ) -> DetectionResult | list[DetectionResult]:
        """Pipeline Mode: Execute checkers sequentially step-by-step. Supports batch processing."""
        runner = self.container.create_pipeline(checker_names=checker_names, strategy=strategy)
        
        if isinstance(data, list):
            file_names = file_name if isinstance(file_name, list) else [None] * len(data)
            targets = [
                InputTarget(buffer=d, file_name=f) if isinstance(d, bytes) else InputTarget(file_path=d, file_name=f)
                for d, f in zip(data, file_names, strict=False)
            ]
            # Simple fallback batch for pipeline since strategy is per-target
            return [runner.run(t) for t in targets]

        target = (
            InputTarget(buffer=data, file_name=file_name)
            if isinstance(data, bytes)
            else InputTarget(file_path=data, file_name=file_name)
        )
        return runner.run(target)

    def detect_parallel(
        self,
        data: bytes | str | list[bytes | str],
        checker_names: list[str] | None = None,
        ensemble_strategy: BaseEnsembleStrategy | None = None,
        file_name: str | list[str] | None = None,
    ) -> DetectionResult | list[DetectionResult]:
        """Parallel Mode: Execute checkers concurrently and aggregate via Ensemble strategy. Supports batch processing."""
        runner = self.container.create_parallel(checker_names=checker_names, ensemble_strategy=ensemble_strategy)
        
        if isinstance(data, list):
            file_names = file_name if isinstance(file_name, list) else [None] * len(data)
            targets = [
                InputTarget(buffer=d, file_name=f) if isinstance(d, bytes) else InputTarget(file_path=d, file_name=f)
                for d, f in zip(data, file_names, strict=False)
            ]
            if hasattr(runner, "run_batch"):
                return runner.run_batch(targets)
            return [runner.run(t) for t in targets]

        target = (
            InputTarget(buffer=data, file_name=file_name)
            if isinstance(data, bytes)
            else InputTarget(file_path=data, file_name=file_name)
        )
        return runner.run(target)

    def detect_normalized(
        self,
        data: bytes | str | list[bytes | str],
        checker_names: list[str] | None = None,
        file_name: str | list[str] | None = None,
        use_parallel: bool = False,
    ) -> NormalizedResult | list[NormalizedResult]:
        """Normalized Mode: Execute detection and return a unified NormalizedResult. Supports batch processing."""
        if use_parallel:
            raw_res = self.detect_parallel(data, checker_names=checker_names, file_name=file_name)
        else:
            raw_res = self.detect_pipeline(data, checker_names=checker_names, file_name=file_name)
            
        if isinstance(raw_res, list):
            return [r.normalize() for r in raw_res]
        return raw_res.normalize()

    # --- Async Standalone Modes ---

    async def detect_magika_async(self, data: bytes | str) -> DetectionResult:
        checker = self.container.get("magika")
        target = InputTarget(buffer=data) if isinstance(data, bytes) else InputTarget(file_path=data)
        return await checker.check_async(target)

    async def detect_magika_paths_async(self, paths: list[str]) -> list[DetectionResult]:
        checker = self.container.get("magika")
        targets = [InputTarget(file_path=p) for p in paths]
        if hasattr(checker, "check_batch_async"):
            return await checker.check_batch_async(targets)
        return [await checker.check_async(t) for t in targets]

    # --- Async Chained & Normalized Modes ---

    async def detect_pipeline_async(
        self,
        data: bytes | str | list[bytes | str],
        checker_names: list[str] | None = None,
        strategy: BasePipelineStrategy | None = None,
        file_name: str | list[str] | None = None,
    ) -> DetectionResult | list[DetectionResult]:
        runner = self.container.create_pipeline(checker_names=checker_names, strategy=strategy)
        if isinstance(data, list):
            file_names = file_name if isinstance(file_name, list) else [None] * len(data)
            targets = [
                InputTarget(buffer=d, file_name=f) if isinstance(d, bytes) else InputTarget(file_path=d, file_name=f)
                for d, f in zip(data, file_names, strict=False)
            ]
            import asyncio
            return await asyncio.gather(*(runner.run_async(t) for t in targets))
        
        target = InputTarget(buffer=data, file_name=file_name) if isinstance(data, bytes) else InputTarget(file_path=data, file_name=file_name)
        return await runner.run_async(target)

    async def detect_parallel_async(
        self,
        data: bytes | str | list[bytes | str],
        checker_names: list[str] | None = None,
        ensemble_strategy: BaseEnsembleStrategy | None = None,
        file_name: str | list[str] | None = None,
    ) -> DetectionResult | list[DetectionResult]:
        runner = self.container.create_parallel(checker_names=checker_names, ensemble_strategy=ensemble_strategy)
        if isinstance(data, list):
            file_names = file_name if isinstance(file_name, list) else [None] * len(data)
            targets = [
                InputTarget(buffer=d, file_name=f) if isinstance(d, bytes) else InputTarget(file_path=d, file_name=f)
                for d, f in zip(data, file_names, strict=False)
            ]
            if hasattr(runner, "run_batch_async"):
                return await runner.run_batch_async(targets)
            import asyncio
            return await asyncio.gather(*(runner.run_async(t) for t in targets))
            
        target = InputTarget(buffer=data, file_name=file_name) if isinstance(data, bytes) else InputTarget(file_path=data, file_name=file_name)
        return await runner.run_async(target)

    async def detect_normalized_async(
        self,
        data: bytes | str | list[bytes | str],
        checker_names: list[str] | None = None,
        file_name: str | list[str] | None = None,
        use_parallel: bool = False,
    ) -> NormalizedResult | list[NormalizedResult]:
        if use_parallel:
            raw_res = await self.detect_parallel_async(data, checker_names=checker_names, file_name=file_name)
        else:
            raw_res = await self.detect_pipeline_async(data, checker_names=checker_names, file_name=file_name)
            
        if isinstance(raw_res, list):
            return [r.normalize() for r in raw_res]
        return raw_res.normalize()
