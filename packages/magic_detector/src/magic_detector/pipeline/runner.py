"""Pipeline Runner for sequential execution of detection modes."""

from magic_detector.interfaces import BaseChecker, BasePipelineStrategy
from magic_detector.models import DetectionResult, InputTarget
from magic_detector.pipeline.strategies import SequentialAccumulatorStrategy


class PipelineRunner:
    """Sequential execution pipeline for detection modes."""

    def __init__(
        self,
        checkers: list[BaseChecker] | None = None,
        strategy: BasePipelineStrategy | None = None,
    ) -> None:
        # DI: Inject checkers and pipeline execution strategy
        self.checkers = checkers or []
        self.strategy = strategy or SequentialAccumulatorStrategy()

    def add_checker(self, checker: BaseChecker) -> "PipelineRunner":
        """Add a checker step to the pipeline."""
        self.checkers.append(checker)
        return self

    def run(self, target: InputTarget) -> DetectionResult:
        """Run all checkers sequentially through the configured strategy."""
        return self.strategy.execute(self.checkers, target)

    async def run_async(self, target: InputTarget) -> DetectionResult:
        """Run all checkers sequentially through the configured strategy asynchronously."""
        # For simplicity in pipelines, if strategy doesn't support async, we wrap the sync execute
        # Real async strategies could be added later.
        import asyncio

        return await asyncio.to_thread(self.strategy.execute, self.checkers, target)

    def run_bytes(self, buffer: bytes, file_name: str | None = None) -> DetectionResult:
        """Convenience method to run pipeline on bytes buffer."""
        return self.run(InputTarget(buffer=buffer, file_name=file_name))

    def run_file(self, file_path: str) -> DetectionResult:
        """Convenience method to run pipeline on file path."""
        return self.run(InputTarget(file_path=file_path))
