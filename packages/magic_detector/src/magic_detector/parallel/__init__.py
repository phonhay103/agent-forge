"""Parallel package export."""

from magic_detector.parallel.runner import ParallelRunner
from magic_detector.parallel.strategies import (
    AdaptiveHybridEnsembleStrategy,
    CompositeEnsembleStrategy,
    ConsensusEnsembleStrategy,
    ConsensusMode,
    PrimaryCategoryEnsembleStrategy,
    FirstMatchEnsembleStrategy,
)

__all__ = [
    "AdaptiveHybridEnsembleStrategy",
    "CompositeEnsembleStrategy",
    "ConsensusEnsembleStrategy",
    "ConsensusMode",
    "ParallelRunner",
    "PrimaryCategoryEnsembleStrategy",
    "FirstMatchEnsembleStrategy",
]
