"""Parallel Execution Runner and Concurrent Ensemble Engine."""

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor

from magic_detector._constants import UNKNOWN
from magic_detector.interfaces import BaseChecker, BaseEnsembleStrategy
from magic_detector.models import DetectionResult, InputTarget
from magic_detector.parallel.strategies import CompositeEnsembleStrategy


class ParallelRunner:
    """Parallel execution runner for concurrent checking and ensemble aggregation."""

    def __init__(
        self,
        checkers: list[BaseChecker] | None = None,
        ensemble_strategy: BaseEnsembleStrategy | None = None,
        max_workers: int = 4,
    ) -> None:
        # DI: Inject checkers, ensemble strategy, and thread pool worker limit
        self.checkers = checkers or []
        self.ensemble_strategy = ensemble_strategy or CompositeEnsembleStrategy()
        self.max_workers = max_workers

    def add_checker(self, checker: BaseChecker) -> "ParallelRunner":
        """Add a checker to parallel suite."""
        self.checkers.append(checker)
        return self

    def run(self, target: InputTarget) -> DetectionResult:
        """Run checkers concurrently using ThreadPoolExecutor and combine via ensemble strategy."""
        active_checkers = [c for c in self.checkers if c.enabled]
        if not active_checkers:
            return DetectionResult(checker_name="parallel_empty", mime_type=UNKNOWN, description=UNKNOWN, )

        start_time = time.perf_counter()

        with ThreadPoolExecutor(max_workers=min(len(active_checkers), self.max_workers)) as executor:
            futures = [executor.submit(c.check, target) for c in active_checkers]
            results = [f.result() for f in futures]

        ensemble_res = self.ensemble_strategy.ensemble(results, target)
        ensemble_res.execution_time_ms = (time.perf_counter() - start_time) * 1000.0
        return ensemble_res

    async def run_async(self, target: InputTarget) -> DetectionResult:
        """Run checkers asynchronously and combine via ensemble strategy."""
        active_checkers = [c for c in self.checkers if c.enabled]
        if not active_checkers:
            return DetectionResult(checker_name="parallel_empty", mime_type=UNKNOWN, description=UNKNOWN, )

        start_time = time.perf_counter()
        tasks = [c.check_async(target) for c in active_checkers]
        results = await asyncio.gather(*tasks)

        ensemble_res = self.ensemble_strategy.ensemble(list(results), target)
        ensemble_res.execution_time_ms = (time.perf_counter() - start_time) * 1000.0
        return ensemble_res

    def run_batch(self, targets: list[InputTarget]) -> list[DetectionResult]:
        """Run checkers concurrently using check_batch and combine via ensemble strategy."""
        active_checkers = [c for c in self.checkers if c.enabled]
        if not active_checkers:
            return [
                DetectionResult(checker_name="parallel_empty", mime_type=UNKNOWN, description=UNKNOWN)
                for _ in targets
            ]

        start_time = time.perf_counter()
        
        with ThreadPoolExecutor(max_workers=min(len(active_checkers), self.max_workers)) as executor:
            # We call the new check_batch method on each checker
            futures = [executor.submit(getattr(c, "check_batch", lambda tgts: [c.check(t) for t in tgts]), targets) for c in active_checkers]
            # results_by_checker is a list (checkers) of lists (results per target)
            results_by_checker = [f.result() for f in futures]

        final_results = []
        for i, target in enumerate(targets):
            target_results = [checker_results[i] for checker_results in results_by_checker]
            ensemble_res = self.ensemble_strategy.ensemble(target_results, target)
            # Roughly distribute execution time
            ensemble_res.execution_time_ms = ((time.perf_counter() - start_time) * 1000.0) / len(targets)
            final_results.append(ensemble_res)

        return final_results

    async def run_batch_async(self, targets: list[InputTarget]) -> list[DetectionResult]:
        """Run checkers concurrently using check_batch_async and combine via ensemble strategy."""
        active_checkers = [c for c in self.checkers if c.enabled]
        if not active_checkers:
            return [
                DetectionResult(checker_name="parallel_empty", mime_type=UNKNOWN, description=UNKNOWN)
                for _ in targets
            ]

        start_time = time.perf_counter()
        
        # We call the new check_batch_async method on each checker
        async def call_checker_batch(c):
            if hasattr(c, "check_batch_async"):
                return await c.check_batch_async(targets)
            return [await c.check_async(t) for t in targets]

        tasks = [call_checker_batch(c) for c in active_checkers]
        results_by_checker = await asyncio.gather(*tasks)

        final_results = []
        for i, target in enumerate(targets):
            target_results = [checker_results[i] for checker_results in results_by_checker]
            ensemble_res = self.ensemble_strategy.ensemble(target_results, target)
            ensemble_res.execution_time_ms = ((time.perf_counter() - start_time) * 1000.0) / len(targets)
            final_results.append(ensemble_res)

        return final_results

    def run_bytes(self, buffer: bytes, file_name: str | None = None) -> DetectionResult:
        """Convenience method to run parallel detection on bytes."""
        return self.run(InputTarget(buffer=buffer, file_name=file_name))

    def run_file(self, file_path: str) -> DetectionResult:
        """Convenience method to run parallel detection on file."""
        return self.run(InputTarget(file_path=file_path))
