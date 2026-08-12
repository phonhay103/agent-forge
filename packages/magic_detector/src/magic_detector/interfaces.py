"""Protocol Interfaces for Checkers, Pipeline Strategies, and Ensemble Strategies."""

from typing import Protocol, runtime_checkable

from magic_detector.models import CheckerCategory, DetectionResult, InputTarget


@runtime_checkable
class BaseChecker(Protocol):
    """Protocol for all detection modes/checkers."""

    name: str
    enabled: bool
    category: CheckerCategory

    def check(self, target: InputTarget) -> DetectionResult:
        """Perform file/buffer check synchronously."""
        ...

    async def check_async(self, target: InputTarget) -> DetectionResult:
        """Perform file/buffer check asynchronously."""
        ...

    def check_batch(self, targets: list[InputTarget]) -> list[DetectionResult]:
        """Perform check for multiple targets (default: sequential processing)."""
        return [self.check(t) for t in targets]

    async def check_batch_async(self, targets: list[InputTarget]) -> list[DetectionResult]:
        """Perform check for multiple targets asynchronously (default: sequential processing)."""
        return [await self.check_async(t) for t in targets]



@runtime_checkable
class BasePipelineStrategy(Protocol):
    """Protocol for executing pipeline steps."""

    def execute(self, checkers: list[BaseChecker], target: InputTarget) -> DetectionResult:
        """Run list of checkers sequentially according to pipeline strategy."""
        ...


@runtime_checkable
class BaseEnsembleStrategy(Protocol):
    """Protocol for combining parallel checker results into a single result."""

    def ensemble(self, results: list[DetectionResult], target: InputTarget) -> DetectionResult:
        """Combine multiple checker results into one consensus DetectionResult."""
        ...
