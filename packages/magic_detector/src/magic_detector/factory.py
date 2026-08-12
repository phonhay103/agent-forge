"""Dependency Injection Container and Factory for MagicDetector."""

from magic_detector.checkers import (
    MagicBytesChecker,
    MagicEncodingChecker,
    MagicExtensionChecker,
    MagicMimeChecker,
    MagikaChecker,
)
from magic_detector.interfaces import BaseChecker, BaseEnsembleStrategy, BasePipelineStrategy
from magic_detector.parallel.runner import ParallelRunner
from magic_detector.pipeline.runner import PipelineRunner


class DetectorContainer:
    """Dependency Injection Container managing detector components and strategies."""

    def __init__(self) -> None:
        self._checkers: dict[str, BaseChecker] = {}

    def register(self, checker: BaseChecker) -> "DetectorContainer":
        """Register a checker into the container."""
        self._checkers[checker.name] = checker
        return self

    def get(self, name: str) -> BaseChecker:
        """Retrieve a checker by name."""
        if name not in self._checkers:
            raise KeyError(f"Checker '{name}' is not registered in container.")
        return self._checkers[name]

    def list_checkers(self) -> list[str]:
        """List names of registered checkers."""
        return list(self._checkers.keys())

    def create_pipeline(
        self,
        checker_names: list[str] | None = None,
        strategy: BasePipelineStrategy | None = None,
    ) -> PipelineRunner:
        """Create a PipelineRunner using registered checkers."""
        selected = [self.get(name) for name in checker_names] if checker_names else list(self._checkers.values())
        return PipelineRunner(checkers=selected, strategy=strategy)

    def create_parallel(
        self,
        checker_names: list[str] | None = None,
        ensemble_strategy: BaseEnsembleStrategy | None = None,
        max_workers: int = 4,
    ) -> ParallelRunner:
        """Create a ParallelRunner using registered checkers."""
        from magic_detector.parallel.strategies import AdaptiveHybridEnsembleStrategy

        selected = [self.get(name) for name in checker_names] if checker_names else list(self._checkers.values())
        return ParallelRunner(
            checkers=selected,
            ensemble_strategy=ensemble_strategy or AdaptiveHybridEnsembleStrategy(),
            max_workers=max_workers,
        )

def create_default_container() -> DetectorContainer:
    """Factory helper to build a pre-configured container with standard python-magic and magika checkers."""
    container = DetectorContainer()
    container.register(MagikaChecker())
    container.register(MagicMimeChecker())
    container.register(MagicBytesChecker())
    container.register(MagicEncodingChecker())
    container.register(MagicExtensionChecker())
    return container
